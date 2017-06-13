import tornado.gen
from base.base_handler import *
from base import utils
from test import *

class TestHandler(BaseHandler):
	def get(self):
		self.render('test.html')

	@arguments_normalization(test_enum=TestEnum, id=utils.type.Int)
	def post(self):
		test_enum = self.get_argument('test_enum')
		id = self.get_argument('id')
		result = self.test_mgr.direct_return(test_enum, id)
		self.write(result)

class AsyncHandler(BaseHandler):
	@tornado.gen.coroutine
	def get(self):
		yield tornado.gen.sleep(0.1)
		self.write('aa')

	@arguments_normalization(coroutine=True, test_enum=TestEnum)
	@tornado.gen.coroutine
	def post(self):
		test_enum = self.get_argument('test_enum')
		s = self.get_argument('str')
		result = yield self.test_mgr.async_return(test_enum, s)
		self.write(result)

handlers = [
	(r'/test', TestHandler),
	(r'/async', AsyncHandler),
]