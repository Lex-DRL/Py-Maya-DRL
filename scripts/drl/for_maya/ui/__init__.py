__author__ = 'Lex Darlog (DRL)'

import sys as _sys

from pymel import core as pm
from drl_common import errors as err
from drl_py23 import (
	str_t as _str_t,
	str_h as _str_h,
)

from .__grid import Grid
from .__progress import Progress

_is_py2 = _sys.version_info[0] == 2

# noinspection PyBroadException
if _is_py2:
	from .__progress_window_py2 import ProgressWindow
else:
	from .__progress_window_py3 import ProgressWindow


class ResIdNotExist(RuntimeError):
	"""
	You're trying to call <resource> function with a key that doesn't exist.
	"""
	def __init__(self, message=''):
		super(ResIdNotExist, self).__init__(message)


class Resource(object):
	"""
	Python class representing resource key-value object.

	To get the actual <uiRes> value of this key, either call value() method or use str() on this object.

	:param key:
		<str> Unique key ID for catalog lookup. E.g.:
			* s_TdialogStrings.rDontSave
	"""
	def __init__(self, key):
		super(Resource, self).__init__()
		self.__key = ''
		self.__set_key(key)

	def __set_key(self, key):
		self.__key = err.NotStringError(key, 'key').raise_if_needed_or_empty()

	@property
	def key(self):
		return self.__key

	@key.setter
	def key(self, val):
		self.__set_key(val)

	def value(self):
		"""
		Call the actual uiRes(key).

		:return: <str/unicode> the key's lookup value
		"""
		try:
			res = pm.mel.uiRes(self.__key)
		except pm.MelError as exc:
			raise ResIdNotExist(exc.message)
		assert isinstance(res, _str_t)
		return res

	def value_formatted(self, *args):
		"""
		Get the value, formatted the same way MEL does.

		:return: <str/unicode> the formatted key's lookup value
		"""
		val = self.value()
		val = pm.format(val, stringArg=list(args))
		assert isinstance(val, _str_t)
		return val

	def __repr__(self):
		return 'ui.Resource(%s)' % repr(self.__key)

	def __str__(self):
		return self.value()

	def __unicode__(self):
		return self.value()


def dialog_str(title=None, msg=None, text=None, button=None, scrollable=False):
	"""
	A wrapper for promptDialog for querying an arbitrary text input.
	"""
	button = button if button else "OK"
	kwargs = {
		kw: v for (kw, v) in {
			'title': title,
			'message': msg,
			'text': text,
			'button': button,
			'cancelButton': "Cancel",
			'dismissString': "cancel",
			'scrollableField': bool(scrollable),
			'style': 'text'
		}.items() if v
	}
	if pm.promptDialog(**kwargs) != "OK":
		return None

	res = pm.promptDialog(q=True, text=True)  # type: str
	return res

