__author__ = 'DRL'

import collections as _c
from pymel.core import ui as _ui, windows as _w

_str_t = (str, unicode)


class ProgressError(Exception):
	pass


ProgressBarTuple = _c.namedtuple('ProgressBarTuple', 'is_main bar')


def _set_str_prop(set_f, val):
	"""
	Sets a property value in a unified way. I.e., ensures it's value is None/str/unicode.

	:param set_f: the function that takes the value and sets the property to it
	:param val: the value
	"""
	if not val:
		set_f(None)
		return
	if isinstance(val, _str_t):
		set_f(val)
		return

	try:
		gen_str = str(val)
	except UnicodeError:
		gen_str = unicode(val)
	set_f(gen_str)


class Progress(object):
	def __init__(
		self, max_displayed=3,
		annotation=None, window_title=None, background=None,
		message_template='{msg} [{cur}/{max}]'
	):
		super(Progress, self).__init__()
		# ensuring the class has the required common variables.
		# sic: Progress is called explicitly instead of self.__class__:
		# this way all the child classes will use the same common values,
		# unless explicitly overridden
		Progress.__get_progresses()
		Progress.__get_window()

		# Progress instance properties:
		self.__max_displayed = 3
		self.__set_max_displayed(max_displayed)
		self.__p_bars = tuple()
		self.__is_main = False
		self.message_template = message_template

		# ProgressBar UI read-only properties:
		self.__min_value = 0
		self.__max_value = 100
		self.__cur_value = 0

		# ProgressBar UI accessible properties:
		self.__annotation = None
		self.__window_title = None
		self.__background = None

		self.__set_annotation_with_check(annotation)
		self.__set_window_title(window_title)
		self.__set_background_with_check(background)

		# annotation-update chooser:
		self.__update_annotation = dict()
		self.__update_annotation[True] = self.__update_status_in_main_bar
		self.__update_annotation[False] = self.__update_annotation_in_window


	# region Common class values

	@staticmethod
	def __get_window():
		"""
		Ensures there's a common private <__window> property and returns it value:
			* None: no window created yet
			* <pymel.core.uitypes.Window> The main multi-level progresses window.
		:return:
		"""
		try:
			return Progress.__window_obj
		except AttributeError:
			nu = None
			Progress.__window_obj = nu
			return nu

	@property
	def __window(self):
		return Progress.__get_window()

	@__window.setter
	def __window(self, value):
		Progress.__window_obj = value

	@property
	def window(self):
		return Progress.__get_window()

	@staticmethod
	def __get_progresses():
		"""
		On the current class (including inherited), creates <__progresses_list>
		if it doesn't exist yet, and returns it.

		:return: <list>
		"""
		try:
			return Progress.__progresses_list
		except AttributeError:
			nu = []
			Progress.__progresses_list = nu
			return nu

	@property
	def __progresses(self):
		"""
		Raw list, for low-level access ONLY.

		It has setter, too. So it allows to modify the list itself,
		and so you need to be **EXTREMELY CAUTIOUS** with it.
		"""
		return Progress.__get_progresses()

	@__progresses.setter
	def __progresses(self, value):
		Progress.__progresses_list = value

	@property
	def progresses(self):
		return tuple(Progress.__get_progresses())

	# endregion

	# region Progress properties

	@property
	def is_main(self):
		is_main = any(b.is_main for b in self.bars)
		self.__is_main = is_main
		return is_main

	@property
	def bars(self):
		"""
		Tuple of **pymel.core.uitypes.MainProgressBar** UI items
		the current progress is displayed in.

		It's tuple for the case of the main progress displayed simultaneously
		in the status bar and the multi-progress window.
		"""
		return self.__p_bars

	def __set_max_displayed(self, value):
		if isinstance(value, int):
			self.__max_displayed = value
			return
		self.__max_displayed = int(value)

	@property
	def max_displayed(self):
		"""
		<int>

		Determines how much progress bars could be shown:

		* 0 or less: no limit, show all of them.
		* 1: show only overall progress (no window will be created)
		*
			2: show only the main progress and the current active one
			(the lowest in call hierarchy)
		* 3 and above: show the main progress and N-1 of the lowest ones.
		"""
		return self.__max_displayed

	@max_displayed.setter
	def max_displayed(self, value):
		self.__set_max_displayed(value)

	# endregion

	# region UI properties

	@property
	def min(self):
		return self.__min_value

	@property
	def max(self):
		return self.__max_value

	@property
	def current(self):
		return self.__cur_value

	def __set_annotation_with_check(self, val):
		def _set(v):
			self.__annotation = v
		_set_str_prop(_set, val)

	@property
	def annotation(self):
		return self.__annotation

	@annotation.setter
	def annotation(self, value):
		self.__set_annotation_with_check(value)

	def annotation_with_progress(self, default='Progress'):
		m = self.annotation or self.window_title or default
		return self.message_template.format(msg=m, cur=self.current, max=self.max)

	def __set_background_with_check(self, val):
		def _set(v):
			self.__background = v
			map(self.__update_background, self.bars)

		if val is None:
			_set(None)
			return
		if isinstance(val, (int, float)):
			val = (val,) * 3
		_set(val)

	@property
	def background(self):
		return self.__background

	@background.setter
	def background(self, value):
		self.__set_background_with_check(value)

	def __set_window_title(self, val):
		def _set(v):
			self.__window_title = v
		_set_str_prop(_set, val)

	@property
	def window_title(self):
		return self.__window_title

	@window_title.setter
	def window_title(self, value):
		self.__set_window_title(value)

	def window_title_with_progress(self, default='Progress'):
		m = self.window_title or self.annotation or default
		return self.message_template.format(msg=m, cur=self.current, max=self.max)

	# endregion

	# region Update UI properties

	def __update_background(self, bar):
		assert isinstance(bar, _ui.ProgressBar)
		bg = self.background
		if bg is None:
			bar.noBackground()
			return
		bar.setEnableBackground()
		bar.setBackgroundColor(bg)

	def __update_min(self, bar):
		bar.setMinValue(self.min)

	def __update_max(self, bar):
		bar.setMaxValue(self.max)

	def __update_current(self, bar):
		bar.setProgress(self.current)

	def __update_annotation_in_window(self, bar):
		"""
		Just a one-case function, with no check. Instead of this, use:

		self.__update_annotation[is_main]
		"""
		bar.setAnnotation(self.annotation_with_progress())

	def __update_status_in_main_bar(self, bar):
		"""
		Just a one-case function, with no check. Instead of this, use:

		self.__update_annotation[is_main]
		"""
		bar.setStatus(self.annotation_with_progress())

	def __update_message(self, is_main, bar):
		self.__update_annotation[is_main](bar)


	def __update_progress_bar(self, p_bar):
		is_main, bar = p_bar
		self.__update_min(bar)
		self.__update_max(bar)
		self.__update_message(is_main, bar)
		if not is_main:
			self.__update_background(bar)

	# TODO: update any other properties

	# endregion

	# region Generate UI

	def __setup_main(self):
		bar = _w.getMainProgressBar()
		p_bar = ProgressBarTuple(True, bar)
		bar.setIsInterruptable(True)
		all_bars = self.__p_bars + (p_bar,)
		self.__p_bars = all_bars
		self.__is_main = True
		map(self.__update_progress_bar, all_bars)

	# TODO: setup window, regular progress-bar, auto-setup any UI for self

	# endregion

	def start(self):
		"""
		Prepare UI for current process and add it to the global progresses list.
		"""
		pr = Progress.__get_progresses()
		if not(self in pr):
			pr.append(self)
		self.__is_main = (pr.index(self) == 0)
		self.__begin()

	def __begin(self):
		"""
		Prepare UI for current process.
		But don't touch the global progresses list.
		"""
		pass

	def end(self):
		"""
		Finish current progress and all of it's children. Remove them from progresses list.
		If they're not completed, interrupt them.
		"""
		pr = self.__progresses
		if not(self in pr):
			self.__interrupt()
			return

		i = pr.index(self)
		removed = pr[i:]  # all the preceding progresses before current
		left = pr[:i]  # current progress and all the rest
		for p in removed:
			p.__interrupt()
		self.__progresses = left

	def __interrupt(self):
		"""
		Interrupt current process. I.e., remove any UI elements
		and stop the working process.
		But don't touch the global progresses list.
		"""
		pass

	def __enter__(self):
		self.start()
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.end()
