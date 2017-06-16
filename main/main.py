import os
import sys
root_dir = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + '/../')
sys.path.insert(0, root_dir)

import logging
import time
import signal
import json
import tornado.web
import tornado.escape
from base import *
from tornado.options import options

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
Assert(options.log_file_prefix, 'Please specify log_file_prefix.')
Assert(options.working_dir, 'Please specify working_dir.')
options.run_parse_callbacks()
os.chdir(options.working_dir)

from base.base_application import run
apps = []
app = run('test', 2000)
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