import os
from base import *

def read_all_text(path, raise_failure=False):
	if not os.path.exists(path):
		Assert(not raise_failure, 'File %s doesn\'t exist.', path)
		return ''
	with open(path, 'r') as f:
		text = f.read()
		return text
	Assert(not raise_failure, 'File %s can\'t be opened.', path)

def read_all_bytes(path, raise_failure=False):
	if not os.path.exists(path):
		Assert(not raise_failure, 'File %s doesn\'t exist.', path)
		return None
	with open(path, 'rb') as f:
		bytes = f.read()
		return bytes
	Assert(not raise_failure, 'File %s can\'t be opened.', path)