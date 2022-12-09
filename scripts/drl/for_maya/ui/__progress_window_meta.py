__author__ = 'Lex Darlog (DRL)'

from maya import cmds
from drl_common import errors as err
from drl_py23 import (
	str_t as _str_t,
	str_h as _str_h,
)


_types = (int, float)


class _ProgressWindowMeta(type):
	"""
	Meta-subclass required to provide static properties.
	"""

	@property
	def progress(cls):
		res = cmds.progressWindow(q=True, progress=True)
		assert isinstance(res, _types)
		return res

	@progress.setter
	def progress(cls, value):
		err.WrongTypeError(value, _types, 'progress value').raise_if_needed()
		assert isinstance(value, _types)
		cmds.progressWindow(e=True, progress=value)
		if value > cls.max or value < cls.min:
			cls.end()

	@property
	def min(cls):
		res = cmds.progressWindow(q=True, min=True)
		assert isinstance(res, _types)
		return res

	@min.setter
	def min(cls, value):
		err.WrongTypeError(value, _types, 'min value').raise_if_needed()
		cmds.progressWindow(e=True, min=value)
		if value > cls.max:
			cls.max = value
		if value > cls.progress:
			cls.progress = value

	@property
	def max(cls):
		res = cmds.progressWindow(q=True, max=True)
		assert isinstance(res, _types)
		return res

	@max.setter
	def max(cls, value):
		err.WrongTypeError(value, _types, 'max value').raise_if_needed()
		cmds.progressWindow(e=True, max=value)
		if value < cls.min:
			cls.min = value
		if value < cls.progress:
			cls.progress = value

	@property
	def interruptable(cls):
		"""
		Returns true if the progress window should respond
		to attempts to cancel the operation.

		The cancel button is disabled if this is set to true.
		"""
		res = cmds.progressWindow(q=True, isInterruptable=True)
		assert isinstance(res, bool)
		return res

	@interruptable.setter
	def interruptable(cls, value):
		if isinstance(value, int):
			value = bool(value)
		err.WrongTypeError(value, bool, 'is-interruptable value').raise_if_needed()
		cmds.progressWindow(e=True, isInterruptable=value)

	@property
	def title(cls):
		res = cmds.progressWindow(q=True, title=True)
		assert isinstance(res, _str_t)
		return res

	@title.setter
	def title(cls, value):
		err.NotStringError(value, 'title name').raise_if_needed()
		cmds.progressWindow(e=True, title=value)

	@property
	def message(cls):
		res = cmds.progressWindow(q=True, status=True)
		assert isinstance(res, _str_t)
		return res

	@message.setter
	def message(cls, value):
		err.NotStringError(value, 'status message').raise_if_needed()
		cmds.progressWindow(e=True, status=value)

	def end(cls):
		"""
		Terminates the progress window.
		"""
		cmds.progressWindow(endProgress=True)
		progress = cls.progress
		assert isinstance(progress, _types)
		max_v = cls.max
		assert isinstance(max_v, _types)
		cls.progress = max_v

	def start(
		cls,
		message='', title='Progress',
		interruptable=True,
		min=0, max=100, start_value=0
	):
		cls.end()
		cmds.progressWindow(
			title=title, status=message,
			isInterruptable=interruptable,
			min=min, max=max, progress=start_value
		)

	def is_cancelled(cls):
		"""
		Returns true if the user has tried to cancel the operation.
		Returns false otherwise.
		"""
		res = cmds.progressWindow(q=True, isCancelled=True)
		assert isinstance(res, bool)
		if res:
			cls.end()
		return res

	def is_active(cls):
		"""
		This is supposed to be used as the condition for <while> loop.
		Returns true if the progress still didn't reach the end.
		Also closes the progress window when it's done.

		:return: bool
		"""
		going = cls.progress < cls.max and not cls.is_cancelled()
		if not going:
			cls.end()
		return going

	def increment(cls, amount=1):
		"""
		Increments the <progress> value by the amount specified.
		"""
		err.WrongTypeError(amount, _types, 'amount').raise_if_needed()
		assert isinstance(amount, _types)
		cmds.progressWindow(e=True, step=amount)
		progress = cls.progress
		assert isinstance(progress, _types)
		if progress >= cls.max:
			cls.end()

	def do_with_each(
		cls,
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
		pw = cls
		cls.start(formatter_f(progress_message, 0, num), progress_title, max=num)
		i = 0
		while cls.is_active():
			cls.message = formatter_f(progress_message, i + 1, num)
			do_with_each_f(items[i], i, res)
			i += 1
			cls.increment()

		return res


try:
	# python 3 style of metaclass declaration:
	class ProgressWindow(metaclass=_ProgressWindowMeta):
		def __init__(
			self,
			message='', title='Progress',
			interruptable=True,
			min=0, max=100, start_value=0
		):
			super(ProgressWindow, self).__init__()
			self.__class__.start(
				message=message, title=title,
				interruptable=interruptable,
				min=min, max=max, start_value=start_value
			)
except SyntaxError:
	# python 2:
	class ProgressWindow(object):
		__metaclass__ = _ProgressWindowMeta

		def __init__(
			self,
			message='', title='Progress',
			interruptable=True,
			min=0, max=100, start_value=0
		):
			super(ProgressWindow, self).__init__()
			self.__class__.start(
				message=message, title=title,
				interruptable=interruptable,
				min=min, max=max, start_value=start_value
			)
