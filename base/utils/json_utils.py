import json
import datetime
import time
from collections import deque
from base import *

# deprecated
class JsonDecoder(json.JSONDecoder):
	def __init__(self, *args, **kwargs):
		return super(JsonDecoder, self).__init__(object_hook=self.dict_to_object, *args, **kwargs)

	def dict_to_object(self, obj):
		if '__intenum__' in obj:
			name = obj['__intenum__']
			module, _sep, name = name.rpartition('.')
			module = __import__(module, fromlist = [name])
			cls = getattr(module, name)
			return cls(obj['__value__'])
		if '__custom_class__' in obj:
			name = obj['__custom_class__']
			module, _sep, name = name.rpartition('.')
			module = __import__(module, fromlist = [name])
			cls = getattr(module, name)
			o = cls()
			o.__dict__ = obj['__value__']
			return o
		if '__datetime__' in obj:
			return datetime.datetime.strptime(obj['__datetime__'], '%Y-%m-%d %H:%M:%S')
		if '__deque__' in obj:
			return deque(obj['__deque__'])
		return obj

# deprecated
class JsonEncoder(json.JSONEncoder):
	def iterencode(self, o, _one_shot=False):
		return super(JsonEncoder, self).iterencode(self.map_int_enum(o), _one_shot)

	def map_int_enum(self, o):
		if isinstance(o, IntEnum):
			return o.name
		if isinstance(o, datetime.datetime):
			return base.utils.time.datetime_to_string(o)
		if isinstance(o, dict):
			return { k: self.map_int_enum(v) for k, v in o.iteritems() }
		if isinstance(o, list):
			all = []
			for v in o:
				all.append(self.map_int_enum(v))
			return all
		if isinstance(o, deque):
			return { '__deque__': list(o) }
		return o

	def default(self, o):
		return { '__custom_class__': '%s.%s' % (o.__module__, o.__class__.__name__),
				 '__value__': self.map_int_enum(o.__dict__) }

class Json(object):
	@classmethod
	def parse(cls, value, except_class=InvalidArguments, except_message='Can\'t convert json.'):
		try:
			return json.loads(value)
		except:
			raise except_class('Invalid json format, %s', except_message)