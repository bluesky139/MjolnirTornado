import tornado.web
import tornado.httpclient
import tornado.concurrent
import threading
import urllib
import json
import os
from tornado.options import options
tornado.httpclient.AsyncHTTPClient.configure(None, max_clients=500)

class SimpleHttpResponse(object):
	def __init__(self):
		self.body  = None
		self.error = None

class Client(object):
	def __init__(self):
		loaded_files = []
		files = os.listdir(os.path.dirname(os.path.realpath(__file__)))
		for file in files:
			if file.startswith('client_') and (file.endswith('.py') or file.endswith('.pyc') or file.endswith('.pyo')):
				name = file[:file.rfind('.')]
				if name in loadedFiles:
					continue
				module = __import__('base.client.' + name, fromlist=[name])
				cls = getattr(module, name)
				setattr(self, name[7:].lower(), cls(self))
				loaded_files.append(name)
		self.cookie = None
		self._base = ClientBase(self)

	def get(self, *args, **kwargs):
		return self._base.get(*args, **kwargs)

	def post(self, *args, **kwargs):
		return self._base.post(*args, **kwargs)

class ClientBase(object):
	def __init__(self, client=None):
		self.client = client
		self.cookie_ = None

	@property
	def cookie(self):
		if self.client is not None:
			return self.client.cookie
		return self.cookie_

	@cookie.setter
	def cookie(self, value):
		if self.client is not None:
			self.client.cookie = value
		self.cookie_ = value

	def prepare(self, headers, callback):
		if self.cookie:
			if headers is None:
				headers = {}
			headers['Cookie'] = self.cookie

		def _callback(response):
			if 'Set-Cookie' in response.headers:
				self.cookie = response.headers['Set-Cookie']
			if callback is not None:
				callback(response)
		return headers, _callback

	def get(self, url, params=None, headers=None, callback=None, **kwargs):
		str_params = ''
		if params:
			for k,v in params.iteritems():
				str_params = '%s%s%s=%s' % (str_params, ('&' if str_params else ''), str(k), str(v) if v else '')
		if str_params:
			url = '%s?%s' % (url, str_params)

		headers, _callback = self.prepare(headers, callback)
		http_client = tornado.httpclient.AsyncHTTPClient()
		return http_client.fetch(url, method='GET', headers=headers, callback=_callback, **kwargs)

	def post(self, url, params, headers=None, callback=None, **kwargs):
		headers, _callback = self.prepare(headers, callback)
		http_client = tornado.httpclient.AsyncHTTPClient()
		return http_client.fetch(url, method='POST', body=urllib.urlencode(params), headers=headers, callback=_callback, **kwargs)

