import os
import sys
root_dir = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + '/../')
sys.path.insert(0, root_dir)

import logging
import time
import redis
import signal
import json
import tornado.web
import tornado.escape
from base import *
from tornado.options import options
options.parse_command_line(None, False)
options.run_parse_callbacks()

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