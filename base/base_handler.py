import tornado.web
import tornado.concurrent
import traceback
import json
import os
import functools
from tornado.options import define, options
from base import *
from base import utils

def arguments_normalization(coroutine=False, **cls_kwargs):
	def handle_normalization(method):
		@functools.wraps(method)
		@tornado.gen.coroutine
		def _normalize(self, *args, **kwargs):
			self.normalized_arguments = {}
			for arg,cls in cls_kwargs.iteritems():
				value = super(BaseHandler, self).get_argument(arg, None)
				if value is not None and value != '':
					self.normalized_arguments[arg] = cls.parse(value, except_class=InvalidArguments) if hasattr(cls, 'parse') else cls(value)
				else:
					self.normalized_arguments[arg] = None
			if coroutine:
				yield method(self, *args, **kwargs)
			else:
				method(self, *args, **kwargs)
		return _normalize
	return handle_normalization

def path_args_normalization(coroutine=False, **cls_kwargs):
	def handle_normalization(method):
		@functools.wraps(method)
		async def _normalize(self, *args, **kwargs):
			args = list(args)
			for i in range(0, len(args)):
				cls = cls_kwargs['_' + str(i)]
				if cls:
					value = args[i]
					args[i] = cls.parse(value, except_class=InvalidArguments) if hasattr(cls, 'parse') else cls(value)
			if coroutine:
				await method(self, *args, **kwargs)
			else:
				method(self, *args, **kwargs)
		return _normalize
	return handle_normalization

class BaseHandler(tornado.web.RequestHandler):
	def initialize(self):
		'''All mgrs are instanticated into self.application, here will put them into handler, for convenient access.
		eg. `ConnectionMgr` class in ``connection_mgr.py``, then you can access it by ``self.connection_mgr``.
		see comments in `Application.init_mgrs()` for more details.
		'''
		for mgr_name, obj in self.application.get_instantiated_mgrs().items():
			setattr(self, mgr_name, obj)
		super(BaseHandler, self).initialize()

	#def set_default_headers(self):
	#	referer = self.request.headers.get('Referer')
	#	if referer:
	#		origin = referer[0:referer.find('/', 10)]
	#		self.set_header('Access-Control-Allow-Origin', origin)
	#		self.set_header('Access-Control-Allow-Credentials', 'true')

	def get_argument(self, name, default=tornado.web._ARG_DEFAULT, strip=True):
		if hasattr(self, 'normalized_arguments') and name in self.normalized_arguments:
			value = self.normalized_arguments[name]
			AssertArgument(default != tornado.web._ARG_DEFAULT or value is not None, 'Missing argument %s', name)
			return value if value is not None else default
		value = super(BaseHandler, self).get_argument(name, default, strip)
		AssertArgument(default != tornado.web._ARG_DEFAULT or value != '', 'Missing argument %s', name)
		return value

	def render(self, template_name, **kwargs):
		template_name = self.application.service + '/templates/' + template_name
		return super(BaseHandler, self).render(template_name, **kwargs)

	def render_base(self, template_name, **kwargs):
		template_name = 'base/templates/' + template_name
		return super(BaseHandler, self).render(template_name, **kwargs)

	def write_error(self, status_code, **kwargs):
		info = kwargs['exc_info'][1] if 'exc_info' in kwargs else None
		if info and hasattr(info, 'log_message'):
			detail = info.log_message
		elif info and hasattr(info, 'message'):
			detail = info.message
		else:
			detail = ''
		self.finish(json.dumps({
			'error': {
				'code': status_code,
				'message': self._reason,
				'detail': str(detail)
			}
		}))