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

		self.module_name_dict = {}
		self.mgr_dict = None
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
		self.init_async()

	def check_options(self):
		pass

	def init_async(self):
		async def _init():
			mgrs = self.get_instantiated_mgrs()
			for name,mgr in mgrs.items():
				try:
					await mgr.init_async()
				except Exception as e:
					logging.error('Init async mgr %s error, %s', name, e)
					raise e
			self.switch_to_alive()
		IOLoop.current().add_callback(_init)

	def init_ui_modules(self):
		'''All ui_modules under [service name]/ui_modules will be loaded at init.
		Only file which ends with 'ui_module.py' will be loaded.
		'''
		ui_modules = {}
		modules = self.get_modules('ui_module')
		for path in modules:
			module = __import__(path, fromlist=['ui_modules'])
			ui_modules.update(module.ui_modules)
		return ui_modules

	def init_handlers(self):
		'''All handlers under [service name]/handlers will be loaded at init.
		Only file which ends with 'handler.py' will be loaded.
		'''
		handlers = []
		modules  = self.get_modules('handler')

		for path in modules:
			module = __import__(path, fromlist=['handlers'])
			if hasattr(module, 'handlers'):
				handlers.extend(module.handlers)

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
		for path in modules:
			module = __import__(path, fromlist=['mgrs'])
			if hasattr(module, 'mgrs'):
				mgrs.extend(module.mgrs)

		mgrs = sorted(mgrs, key=lambda x:x[1])
		for mgr in mgrs:
			mgr  = mgr[0]
			name = mgr.__name__
			obj  = mgr(self)
			setattr(self, utils.type.String.lower_upper_with_underscore(name), obj)

	def get_modules(self, module_name):
		modules = self.module_name_dict.get(module_name)
		if modules is not None:
			return modules

		modules = []
		path = self.root_dir + '/base/' + module_name + 's'
		if os.path.exists(path):
			dirs = os.listdir(path)
			for dir in dirs:
				if dir.endswith(module_name + '.py') or dir.endswith(module_name + '.pyc') or dir.endswith(module_name + '.pyo'):
					name = dir[:dir.rfind('.')]
					modules.append('base.' + module_name + 's.' + name)

		path = self.root_dir + '/' + self.service + '/' + module_name + 's'
		if os.path.exists(path):
			dirs = os.listdir(path)
			for dir in dirs:
				if dir.endswith(module_name + '.py') or dir.endswith(module_name + '.pyc') or dir.endswith(module_name + '.pyo'):
					name = dir[:dir.rfind('.')]
					modules.append(self.service + '.' + module_name + 's.' + name)
		self.module_name_dict[module_name] = modules
		return modules

	def get_instantiated_mgrs(self):
		if self.mgr_dict is not None:
			return self.mgr_dict

		modules = self.get_modules('mgr')
		mgrs = []
		for path in modules:
			module = __import__(path, fromlist=['mgrs'])
			if hasattr(module, 'mgrs'):
				mgrs.extend(module.mgrs)

		self.mgr_dict = {}
		for mgr in mgrs:
			mgr  = mgr[0]
			name = mgr.__name__
			mgr_name = utils.type.String.lower_upper_with_underscore(name)
			obj  = getattr(self, mgr_name)
			self.mgr_dict[mgr_name] = obj
		return self.mgr_dict

	def switch_to_alive(self):
		logging.info('%s is listening at %d' % (self.service, self.port))
		self.listen(self.port, xheaders=True)

	async def shutdown(self):
		pass

def run(service, port):
	if not options.local_debug:
		logging.info('\n--\nRun ' + service)
		for k,v in options.items():
			logging.info('[Option] ' + k + ' = ' + str(v))
		logging.info('--\n')

	# Load specific app from module if available.
	app_cls = Application
	try:
		module = __import__(service + '.application', fromlist=['Application'])
		app_cls = getattr(module, 'Application')
	except:
		pass

	application = app_cls(service, port)
	return application
