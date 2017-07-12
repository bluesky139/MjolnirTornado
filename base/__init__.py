import tornado.web
import tornado.ioloop
import logging
import enum
import os
import cPickle
import time
import sys
from tornado.options import define

define('local_debug', default=True, type=bool, help='Only for local debug.')
define('working_dir', default='')
define('cookie_secret', default='3loE34zKXIBGaYpkLp9XdT91q')
define('service_name', default='', help='Not precise in local debug.')
define('port', 0, type=int, help='Not precise in local debug, use ``self.application.port`` instead.')

root_dir = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + '/../')
def combine_path(path):
	if path.startswith(root_dir):
		return path
	if not path.startswith('/'):
		return root_dir + '/' + path
	return root_dir + path

class HTTPError_(tornado.web.HTTPError):
	def __init__(self, code, tag, msg, *args):
		super(HTTPError_, self).__init__(code, tag + (msg % args if args else msg))

class HTTPError(HTTPError_):
	def __init__(self, code, msg, *args):
		return super(HTTPError, self).__init__(code, '[HTTPError] ', msg, *args)

class InvalidArguments(HTTPError_):
	def __init__(self, msg, *args):
		return super(InvalidArguments, self).__init__(400, '[InvalidArguments] ', msg, *args)

class UnauthorizedError(HTTPError_):
	def __init__(self, msg, *args):
		return super(UnauthorizedError, self).__init__(401, '[UnauthorizedError] ', msg, *args)

class InvalidOperation(HTTPError_):
	def __init__(self, msg, *args):
		return super(InvalidOperation, self).__init__(403, '[InvalidOperation] ', msg, *args)

class NotFound(HTTPError_):
	def __init__(self, msg, *args):
		return super(NotFound, self).__init__(404, '[NotFound] ', msg, *args)

class ConflictOperation(HTTPError_):
	def __init__(self, msg, *args):
		return super(ConflictOperation, self).__init__(409, '[ConflictOperation] ', msg, *args)

class Unsupported(HTTPError_):
	def __init__(self, msg, *args):
		return super(Unsupported, self).__init__(415, '[Unsupported] ', msg, *args)

class OperationFailed(HTTPError_):
	def __init__(self, msg, *args):
		return super(OperationFailed, self).__init__(500, '[OperationFailed] ', msg, *args)

class NotImplemented(HTTPError_):
	def __init__(self, msg = '', *args):
		return super(OperationFailed, self).__init__(500, '[NotImplemented] ', msg, *args)

class TimeoutError(HTTPError_):
	def __init__(self, msg, *args):
		return super(TimeoutError, self).__init__(502, '[TimeoutError] ', msg, *args)

class ServiceUnavailable(HTTPError_):
	def __init__(self, msg, *args):
		return super(ServiceUnavailable, self).__init__(503, '[ServiceUnavailable] ', msg, *args)

class AssertError(HTTPError_):
	def __init__(self, msg, *args):
		return super(AssertError, self).__init__(500, '[AssertError] ', msg, *args)

def Assert(condition, msg, *args, **kwargs):
	if not condition:
		exceptClass = kwargs['except_class'] if kwargs.has_key('except_class') else AssertError
		raise exceptClass(msg, *args)

def AssertArgument(condition, msg, *args):
	if not condition:
		raise InvalidArguments(msg, *args)

def AssertOperation(condition, msg, *args):
	if not condition:
		raise InvalidOperation(msg, *args)

def AssertConflict(condition, msg, *args):
	if not condition:
		raise ConflictOperation(msg, *args)

def AssertWarning(condition, msg, *args):
	if not condition:
		logging.warning(msg, *args)


@enum.unique
class IntEnum(enum.IntEnum):
	def __str__(self):
		return self.name

	@property
	def str(self):
		return self.__str__()

	@classmethod
	def parse(cls, value, except_class=InvalidArguments, except_message='Can\'t convert enum.'):
		if isinstance(value, cls):
			return value
		elif isinstance(value, int):
			try:
				return cls(value)
			except:
				raise except_class(except_message + '[Enum not found, %s]' % value)
		elif isinstance(value, str) or isinstance(value, unicode):
			a = getattr(cls, value, None)
			if a is None:
				try:
					value = int(value)
					a = cls(value)
				except:
					pass
			if a is None and except_class:
				raise except_class(except_message + '[Enum not found, %s]' % value)
			return a
		else:
			if except_class:
				raise except_class(except_message + '[Enum not found, %s]' % value)

	@classmethod
	def to_name_list(cls, exclude=None):
		names = []
		for e in cls:
			if e != exclude and not e.name.startswith('_'):
				names.append(e.name)
		return names

	@classmethod
	def to_enum_list(cls, exclude=None):
		enums = []
		for e in cls:
			if e != exclude and not e.name.startswith('_'):
				enums.append(e)
		return enums

	@classmethod
	def first_element(cls):
		for c in cls:
			return c

_all_services = None
def get_all_services():
	global _all_services
	if _all_services is None:
		dirs = os.listdir(root_dir)
		dirs = filter(lambda d: not d.startswith('.') and not d.startswith('_') 
				   and d != 'base' and d != 'main'
				   and os.path.isdir(root_dir + '/' + d), dirs)
		_all_services = dirs
	return _all_services