import tornado.web
import logging

class TestModule(tornado.web.UIModule):
	def render(self, path, **kwargs):
		return 'test ui module, ' + path

class TemplateBaseModule(tornado.web.TemplateModule):
	def render(self, path, **kwargs):
		logging.info('TemplateBaseModule from test.')
		path = 'base/templates/' + path
		return super(TemplateBaseModule, self).render(path, **kwargs)

ui_modules = {
	'Test': TestModule,

	# Override base ui_modules by service ui_modules with same name
	#'TemplateBase': TemplateBaseModule
}