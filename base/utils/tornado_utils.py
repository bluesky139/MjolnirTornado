import tornado.gen
import datetime
from base import *

@tornado.gen.coroutine
def TimeoutTask(seconds, timeout_callback, func, *args, **kwargs):
	future = tornado.gen.Task(func, *args, **kwargs)
	try:
		result = yield tornado.gen.with_timeout(datetime.timedelta(seconds=seconds), future)
		raise tornado.gen.Return(result)
	except tornado.gen.TimeoutError:
		if timeout_callback is not None:
			timeout_callback()
		raise TimeoutError('TimeoutTask')