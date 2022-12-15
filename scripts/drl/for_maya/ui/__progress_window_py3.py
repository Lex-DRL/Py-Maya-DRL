# encoding: utf-8

from .__progress_window_meta import _ProgressWindowMeta


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
