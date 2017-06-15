from base.base_handler import *

class WelcomeHandler(BaseHandler):
	def get(self):
		self.write('Welcome to %s service.' % self.application.service)

handlers = [
	(r'/', WelcomeHandler),
]