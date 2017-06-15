import tornado.web

class TestModule(tornado.web.UIModule):
	def render(self, path, **kwargs):
		return 'test ui module, ' + path

ui_modules = {
	'Test': TestModule
}