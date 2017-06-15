import os
import sys
import urllib
import logging
import json
import collections
import tornado.web
import tornado.httpclient
from tornado.options import define, options
from tornado.ioloop import IOLoop
from base import *
from base import utils

class Application(tornado.web.Application):
	'''One application only serve one service.
	'''
	def __init__(self, service, port):
		self.root_dir = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + '/../')
		self.service  = service
		self.port	  = port

		self.initial_callbacks = {}
		self.check_options()

		#sys.path.append(self.root_dir + '/' + service)
		self.init_mgrs()
		
		self.ui_modules_ = self.init_ui_modules()
		self.handlers_ = self.init_handlers()
		settings = dict(
			template_path = self.root_dir,
			static_path   = self.root_dir + '/' + service + '/static',
			ui_modules    = self.ui_modules_,
			cookie_secret = options.cookie_secret,
			autoescape    = None
		)
		super(Application, self).__init__(self.handlers_, **settings)
		self.wait_check_end()

	def check_options(self):
		pass

	def new_initial_callback(self, name):
		def callback(*args, **kwargs):
			ok  = args[0] if args and len(args) > 1 else True
			msg = args[1] if args and len(args) > 1 else None
			if ok:
				logging.info('End initial callback %s' % name)
				self.initial_callbacks.pop(callback)
			else:
				raise AssertError('Initial error, %s' % msg)
		self.initial_callbacks[callback] = name
		logging.info('New initial callback %s' % name)
		return callback

	def wait_check_end(self):
		'''Some check/connect need time, wait here a while.
		'''
		@tornado.gen.coroutine
		def _wait():
			while self.initial_callbacks:
				logging.info('Initial callbacks remain len %d, names %s' % (len(self.initialCallbacks), ','.join(self.initialCallbacks.values())))
				yield tornado.gen.sleep(1)
			self.switch_to_alive()

		IOLoop.current().add_callback(_wait)

	def init_ui_modules(self):
		ui_modules = {}
		modules = self.get_modules('ui_module')
		for name,path in modules.iteritems():
			module = __import__(path, fromlist=['ui_modules'])
			ui_modules.update(module.ui_modules)
		return ui_modules

	def init_handlers(self):
		'''All handlers under [service name]/handlers will be loaded at init.
		Only file which ends with 'handler.py' will be loaded.
		'''
		handlers = []
		modules  = self.get_modules('handler')

		for name,path in modules.iteritems():
			module = __import__(path, fromlist=['handlers'])
			for handler in module.handlers:
				handlers = filter(lambda h: h[0] != handler[0], handlers)
				handlers.append(handler)

		handlers.append((r'/static_base/(.+)', tornado.web.StaticFileHandler, dict(path=self.root_dir + '/base/static')))
		return handlers

	def get_handlers(self):
		return self.handlers_

	def init_mgrs(self):
		'''All mgrs under [service name]/mgrs and base/mgrs will be treated as single instance mgr and instantiated.
		Only file which ends with 'mgr.py' will be instantiated.
		eg. `ConnectionMgr` class in ``connection_mgr.py``, then you can access it by ``self.application.connection_mgr``.
		In your handler, you can access it by ``self.connection_mgr``, see comments in `BaseHandler.initialize()` for more details.
		'''
		modules = self.get_modules('mgr')
		mgrs = []
		for name,path in modules.iteritems():
			mgr = __import__(path, fromlist=['mgrs'])
			mgrs.extend(mgr.mgrs)

		mgrs = sorted(mgrs, cmp = lambda x,y:cmp(x[1],y[1]))
		for mgr in mgrs:
			mgr  = mgr[0]
			name = mgr.__name__
			obj  = mgr(self)
			setattr(self, utils.type.String.lower_upper_with_underscore(name), obj)

	def get_modules(self, module_name):
		modules = collections.OrderedDict()
		path = self.root_dir + '/base/' + module_name + 's'
		if os.path.exists(path):
			dirs = os.listdir(path)
			for dir in dirs:
				if dir.endswith(module_name + '.py') or dir.endswith(module_name + '.pyc') or dir.endswith(module_name + '.pyo'):
					name = dir[:dir.rfind('.')]
					if name in modules:
						continue
					Assert(not modules.has_key(name), 'Duplicated ' + module_name + ' ' + name)
					modules[name] = 'base.' + module_name + 's.' + name

		path = self.root_dir + '/' + self.service + '/' + module_name + 's'
		if os.path.exists(path):
			dirs = os.listdir(path)
			sub_modules = {}
			for dir in dirs:
				if dir.endswith(module_name + '.py') or dir.endswith(module_name + '.pyc') or dir.endswith(module_name + '.pyo'):
					name = dir[:dir.rfind('.')]
					if name in sub_modules:
						continue
					Assert(not sub_modules.has_key(name), 'Duplicated ' + module_name + ' ' + name)
					sub_modules[name] = self.service + '.' + module_name + 's.' + name
			modules.update(sub_modules)
		return modules

	def switch_to_alive(self):
		logging.info('%s is listening at %d' % (self.service, self.port))
		self.listen(self.port, xheaders=True)

def run(service, port):
	if not options.local_debug:
		logging.info('\n--\nRun ' + service)
		for k,v in options.items():
			logging.info('[Option] ' + k + ' = ' + str(v))
		logging.info('--\n')

	# Load specific app from module if available.
	app_cls = Application
	try:
		module = __import__(service + '.Application', fromlist=['Application'])
		app_cls = getattr(module, 'Application')
	except:
		pass

	application = app_cls(service, port)
	return application
