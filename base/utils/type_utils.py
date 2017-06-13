import re
from base import *

class List(object):
	@classmethod
	def parse(cls, value, except_class=InvalidArguments, except_message='Can\'t convert list.'):
		try:
			return value.split('|')
		except:
			raise except_class('Invalid list format, %s', except_message)

class Int(object):
	@classmethod
	def parse(cls, value, except_class=InvalidArguments, except_message='Can\'t convert int.'):
		try:
			return int(value)
		except:
			raise except_class('Invalid int, %s', except_message)

class Float(object):
	@classmethod
	def parse(cls, value, except_class=InvalidArguments, except_message='Can\'t convert float.'):
		try:
			return float(value)
		except:
			raise except_class('Invalid float, %s', except_message)

class Bool(object):
	@classmethod
	def parse(cls, value, except_class=InvalidArguments, except_message='Can\'t convert bool.'):
		return value in [True, 'True', 'true', 'TRUE', '1', 1]

class Dict(object):
	@classmethod
	def make_sure_key(cls, value, key, default_value=''):
		if not value.has_key(key):
			value[key] = default_value

class NoConvert(object):
	@classmethod
	def parse(cls, value, except_class=None, except_message=None):
		return value

class String(object):
	VALID_STR_LETTER     = int('001', 2)
	VALID_STR_DIGIT      = int('010', 2)
	VALID_STR_UNDERSCORE = int('100', 2)
	_valid_str_regs = {}
	@classmethod
	def validate(cls, s, flag, except_class=InvalidArguments, except_message='Invalid string'):
		global _valid_str_regs
		if not _valid_str_regs.has_key(flag):
			reg = r'^['
			if flag & cls.VALID_STR_LETTER:
				reg += r'a-zA-Z'
			if flag & cls.VALID_STR_DIGIT:
				reg += r'\d'
			if flag & cls.VALID_STR_UNDERSCORE:
				reg += r'_'
			reg += r']+$'
			reg = re.compile(reg)
			_valid_str_regs[flag] = reg

		reg = _valid_str_regs[flag]
		if reg.match(s) is None:
			raise except_class('%s, %s' % (except_message, s))
			return False
		return True

	@classmethod
	def lower_upper_with_underscore(cls, s):
		return ''.join('_' + c.lower() if c.isupper() else c for c in s).lstrip('_')