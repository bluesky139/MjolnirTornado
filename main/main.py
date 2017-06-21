import os
import sys
root_dir = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + '/../')
sys.path.insert(0, root_dir)

import logging
import time
import signal
import json
import re
import tornado.web
import tornado.escape
import base.base_application
from base import *
from base import utils
from base.client import *
from tornado.options import options

arg_service = None
for arg in sys.argv:
	match = re.match(r'^\-\-service_name=(.+)$', arg)
	if match:
		arg_service = match.group(1)
		break

# Load service module first, all service specific defines should be wrote in __init__.py
if arg_service:
	__import__(arg_service)
else:
	services = get_all_services()
	for service in services:
		__import__(service)

options.parse_command_line(None, False)
options.log_rotate_mode = 'time'
options.log_rotate_when = 'midnight'
options.log_rotate_interval = 1
options.log_file_num_backups = 30
if options.local_debug:
	logging.getLogger().addHandler(logging.StreamHandler())
	log_dir = root_dir + '/_log'
	if not os.path.exists(log_dir):
		os.mkdir(log_dir)
	options.log_file_prefix = log_dir + '/' + str(options.port) + '.log'
	options.working_dir = root_dir
	options.domain = 'example.com'
	options.region = 'local'
Assert(options.log_file_prefix, 'Please specify log_file_prefix.')
Assert(options.working_dir, 'Please specify working_dir.')
Assert(options.domain, 'Please specify domain.')
Assert(options.region, 'Please specify region.')
options.run_parse_callbacks()
os.chdir(options.working_dir)

if options.local_debug:
	class FakeNginxHandler(tornado.web.RequestHandler):
		@tornado.gen.coroutine
		def get(self, *args, **wargs):
			client = Client()
			yield self.handle(client.get)

		@tornado.gen.coroutine
		def post(self, *args, **wargs):
			client = Client()
			yield self.handle(client.post)

		@tornado.gen.coroutine
		def handle(self, method):
			headers = self.request.headers
			headers.pop('If-None-Match', None)
			headers.pop('If-Modified-Since', None)
			host = self.request.host.split(':')[0]
			AssertOperation(nginx_forwards.has_key(host), 'Unknown host %s' % host)

			args = {}
			for k,v in self.request.arguments.iteritems():
				args[k] = tornado.escape.url_escape(v[0]) if self.request.method == 'GET' else v[0]
			ret = yield method('http://%s:%d%s' % (host, nginx_forwards[host], self.request.path), 
					  args , headers, raise_error=False, follow_redirects=False)
			self._headers = ret.headers
			self.set_status(ret.error.code)
			self.write(ret.body)

		def write_error(self, status_code, **kwargs):
			info = kwargs['exc_info'][1] if 'exc_info' in kwargs else None
			if info and hasattr(info, 'log_message'):
				detail = info.log_message
			elif info and hasattr(info, 'message'):
				detail = info.message
			else:
				detail = ''
			self.finish(detail)

	nginx_app = tornado.web.Application([
		('/(.*)', FakeNginxHandler)
	])
	nginx_app.listen(80)
	#nginx_app.listen(443, ssl_options={
	#	'certfile': root_dir + '/ssl.crt',
	#	'keyfile' : root_dir + '/ssl.key',
	#})


if options.local_debug:
	nginx_forwards = {}
	def run(service, port):
		nginx_forwards[utils.url.get_service_host(service)] = port
		nginx_forwards[utils.url.get_service_host_internal(service)] = port
		return base.base_application.run(service, port)
else:
	from base.base_application import run

apps = []
if options.local_debug:
	services = get_all_services()
	for i,service in enumerate(services):
		app = run(service, 2000 + i)
		apps.append(app)
else:
	app = run(options.service_name, options.port)
	apps.append(app)

def signal_handler(signal, frame):
	logging.warning('Caught signal ' + str(signal))
	tornado.ioloop.IOLoop.current().add_callback(shutdown)

def shutdown():
	ioLoop = tornado.ioloop.IOLoop.current()
	@tornado.gen.coroutine
	def check_shutdown():
		for app in reversed(apps):
			logging.info('Service %s is off.' % app.service)
		ioLoop.stop()
	ioLoop.add_callback(check_shutdown)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT,  signal_handler)

tornado.ioloop.IOLoop.current().start()
logging.info('Exit.')