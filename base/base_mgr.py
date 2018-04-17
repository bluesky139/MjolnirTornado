class BaseMgr(object):
	def __init__(self, application):
		self.application = application

	async def init_async(self):
		pass