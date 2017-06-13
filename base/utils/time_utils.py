import datetime
import time
from base import *

def datetime_to_timestamp(dt):
	return int(time.mktime(dt.timetuple()))

def timestamp_to_datetime(timestamp):
	return datetime.datetime.fromtimestamp(int(timestamp))

def datetime_to_string(dt):
	return dt.strftime('%Y-%m-%d %H:%M:%S')

def string_to_datetime(s):
	return datetime.datetime.strptime(s, '%Y-%m-%d %H:%M:%S')

class DateTime(object):
	@classmethod
	def parse(cls, value, except_class=InvalidArguments, except_message='Can\'t convert datetime.'):
		try:
			return string_to_datetime(value)
		except:
			raise except_class('Invalid datatime string %s', value)

