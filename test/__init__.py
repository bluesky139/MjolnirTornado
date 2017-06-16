from base import *
from tornado.options import define

define('test_define_a', default='')

class TestEnum(IntEnum):
	E1 = 1
	E2 = 2
	E3 = 3