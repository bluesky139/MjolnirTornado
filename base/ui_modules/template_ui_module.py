import tornado.web

class TemplateModule(tornado.web.TemplateModule):
	def render(self, path, **kwargs):
		path = self.handler.application.service + '/templates/' + path
		return super(TemplateModule, self).render(path, **kwargs)

class TemplateBaseModule(tornado.web.TemplateModule):
	def render(self, path, **kwargs):
		path = 'base/templates/' + path
		return super(TemplateBaseModule, self).render(path, **kwargs)

ui_modules = {
	'Template': TemplateModule,
	'TemplateBase': TemplateBaseModule
}