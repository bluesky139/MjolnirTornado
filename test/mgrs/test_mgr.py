from base.base_mgr import *
import tornado.gen

class TestMgr(BaseMgr):
	def __init__(self, application):
		super(TestMgr, self).__init__(application)

	def direct_return(self, test_enum, id):
		return 'direct result, %s, %d' % (test_enum.name, id)

	@tornado.gen.coroutine
	def async_return(self, test_enum, s):
		yield tornado.gen.sleep(0.1)
		raise tornado.gen.Return('async return, %s, %s' % (test_enum.name, s))

mgrs = [
	(TestMgr, 1000),
]