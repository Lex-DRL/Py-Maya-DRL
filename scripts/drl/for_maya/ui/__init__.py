__author__ = 'DRL'

from maya import cmds
from pymel import core as pm
from drl_common import errors as err

from . import dialogs

_types = (int, float)
_str_types = (str, unicode)


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

	:param key: <str>  Unique key ID for catalog lookup. E.g.:

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
		assert isinstance(res, _str_types)
		return res

	def value_formatted(self, *args):
		"""
		Get the value, formatted the same way MEL does.

		:return: <str/unicode> the formatted key's lookup value
		"""
		val = self.value()
		val = pm.format(val, stringArg=list(args))
		assert isinstance(val, _str_types)
		return val

	def __repr__(self):
		return 'ui.Resource(%s)' % repr(self.__key)

	def __str__(self):
		return self.value()

	def __unicode__(self):
		return self.value()


def resource(key):
	"""
	Python version of Maya's <uiRes> MEL function.

	:param key: <str> Unique key ID for catalog lookup
	:return: <str> the key's lookup value
	"""
	return Resource(key).value()


class ProgressWindow(object):
	class __meta(type):
		"""
		Meta-subclass required to provide static properties.
		"""

		@property
		def progress(self):
			res = cmds.progressWindow(q=True, progress=True)
			assert isinstance(res, _types)
			return res

		@progress.setter
		def progress(self, value):
			err.WrongTypeError(value, _types, 'progress value').raise_if_needed()
			assert isinstance(value, _types)
			cmds.progressWindow(e=True, progress=value)
			if value > self.max or value < self.min:
				ProgressWindow.end()

		@property
		def min(self):
			res = cmds.progressWindow(q=True, min=True)
			assert isinstance(res, _types)
			return res

		@min.setter
		def min(self, value):
			err.WrongTypeError(value, _types, 'min value').raise_if_needed()
			cmds.progressWindow(e=True, min=value)
			if value > self.max:
				self.max = value
			if value > self.progress:
				self.progress = value

		@property
		def max(self):
			res = cmds.progressWindow(q=True, max=True)
			assert isinstance(res, _types)
			return res

		@max.setter
		def max(self, value):
			err.WrongTypeError(value, _types, 'max value').raise_if_needed()
			cmds.progressWindow(e=True, max=value)
			if value < self.min:
				self.min = value
			if value < self.progress:
				self.progress = value

		@property
		def interruptable(self):
			"""
			Returns true if the progress window should respond
			to attempts to cancel the operation.

			The cancel button is disabled if this is set to true.
			"""
			res = cmds.progressWindow(q=True, isInterruptable=True)
			assert isinstance(res, bool)
			return res

		@interruptable.setter
		def interruptable(self, value):
			if isinstance(value, int):
				value = bool(value)
			err.WrongTypeError(value, bool, 'is-interruptable value').raise_if_needed()
			cmds.progressWindow(e=True, isInterruptable=value)

		@property
		def title(self):
			res = cmds.progressWindow(q=True, title=True)
			assert isinstance(res, _str_types)
			return res

		@title.setter
		def title(self, value):
			err.NotStringError(value, 'title name').raise_if_needed()
			cmds.progressWindow(e=True, title=value)

		@property
		def message(self):
			res = cmds.progressWindow(q=True, status=True)
			assert isinstance(res, _str_types)
			return res

		@message.setter
		def message(self, value):
			err.NotStringError(value, 'status message').raise_if_needed()
			cmds.progressWindow(e=True, status=value)

	__metaclass__ = __meta

	def __init__(
		self,
		message='', title='Progress',
		interruptable=True,
		min=0, max=100, start_value=0
	):
		super(ProgressWindow, self).__init__()
		self.__class__.end()
		cmds.progressWindow(
			title=title, status=message,
			isInterruptable=interruptable,
			min=min, max=max, progress=start_value
		)

	@staticmethod
	def is_cancelled():
		"""
		Returns true if the user has tried to cancel the operation.
		Returns false otherwise.
		"""
		res = cmds.progressWindow(q=True, isCancelled=True)
		assert isinstance(res, bool)
		if res:
			ProgressWindow.end()
		return res

	@staticmethod
	def is_active():
		"""
		This is supposed to be used as the condition for <while> loop.
		Returns true if the progress still didn't reach the end.
		Also closes the progress window when it's done.

		:return: bool
		"""
		going = ProgressWindow.progress < ProgressWindow.max and not ProgressWindow.is_cancelled()
		if not going:
			ProgressWindow.end()
		return going

	@staticmethod
	def increment(amount=1):
		"""
		Increments the <progress> value by the amount specified.
		"""
		err.WrongTypeError(amount, _types, 'amount').raise_if_needed()
		assert isinstance(amount, _types)
		cmds.progressWindow(e=True, step=amount)
		progress = ProgressWindow.progress
		assert isinstance(progress, _types)
		if progress >= ProgressWindow.max:
			ProgressWindow.end()

	@staticmethod
	def end():
		"""
		Terminates the progress window.
		"""
		cmds.progressWindow(endProgress=True)
		progress = ProgressWindow.progress
		assert isinstance(progress, _types)
		max_v = ProgressWindow.max
		assert isinstance(max_v, _types)
		ProgressWindow.progress = max_v

	@staticmethod
	def do_with_each(
		items, do_with_each_f,
		progress_title='Performing task...', progress_message='Progress: {0} / {1}',
		progress_message_formatter_f=None
	):
		"""
		This is high-level function, allowing you to easily perform the same action
		on the entire list of elements, displaying the progress.

		:param items: <list/tuple> of elements to perform action on
		:param do_with_each_f:
			The actual <function> that does what you need.

			It's signature:

			:arg: current element in the list
			:arg: <int> index of the current element
			:arg:
				the resulting <list>.

				I.e., the list you may want to add the current element to
				if some condition is met.
		:param progress_title: <string> The title of the window.
		:param progress_message: <string> The message that will be formatted.
		:param progress_message_formatter_f:
			A custom <function> that performs the actual formatting of the message.

			It's signature:

			:arg: <string> the formatted message
			:arg: <int> number of the current item (i + 1)
			:arg: <int> total number of items
		:return:
			<list>, that you can add anything to by accessing
			the last argument of the <do_with_each_f>.
		"""
		import inspect

		err.WrongTypeError(items, (list, tuple)).raise_if_needed()

		num = len(items)
		if num == 0:
			return []

		err.NotStringError(progress_title, 'progress_title').raise_if_needed()
		err.NotStringError(progress_message, 'progress_message').raise_if_needed()

		def _error_check_main_f():
			if not callable(do_with_each_f):
				raise err.WrongTypeError(
					do_with_each_f,
					var_name="do_with_each_f",
					types_name="callable"
				)
			func_args = inspect.getargspec(do_with_each_f).args
			if not(isinstance(func_args, (list, tuple)) and len(func_args) == 3):
				raise ValueError(
					'The given <do_with_each_f> requires exactly 3 arguments. Got: '
					+ repr(func_args)
				)

		def _error_check_formatter_f(formatter):
			if formatter is None:
				# formatter isn't defined, let's use the default one
				formatter = lambda msg, cur, total: msg.format(cur, total)
				return formatter

			# formatter is defined, but... :
			if not callable(formatter):
				# ... it's not callable
				raise err.WrongTypeError(
					formatter,
					var_name="progress_message_formatter_f",
					types_name="callable"
				)
			func_args = inspect.getargspec(formatter).args
			if not(isinstance(func_args, (list, tuple)) and len(func_args) == 3):
				# ... it has the wrong number of arguments
				raise ValueError(
					'The given <progress_message_formatter_f> requires exactly 3 arguments. Got: '
					+ repr(func_args)
				)
			return formatter

		_error_check_main_f()
		formatter_f = _error_check_formatter_f(progress_message_formatter_f)

		res = list()
		pw = ProgressWindow
		pw(formatter_f(progress_message, 0, num), progress_title, max=num)
		i = 0
		while pw.is_active():
			pw.message = formatter_f(progress_message, i + 1, num)
			do_with_each_f(items[i], i, res)
			i += 1
			pw.increment()

		return res