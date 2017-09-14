__author__ = 'DRL'



from pymel.core import (
	uitypes as _ui,
	windows as _w
)

_str_t = (str, unicode)


class ProgressError(Exception):
	pass


# region IsMainProgressBar named-tuple

try:
	# no actual Python 3.x support. Just to allow type hinting:
	from typing import *
	IsMainProgressBar = NamedTuple(
		'IsMainProgressBar',
		[
			('is_main', bool),
			('bar', _ui.ProgressBar),
		]
	)
except ImportError:
	import collections as __c
	IsMainProgressBar = __c.namedtuple('IsMainProgressBar', 'is_main bar')

# endregion


# region ProgressBarsCouple class

class ProgressBarsCouple(object):
	"""
	* When iterated, IsMainProgressBar is returned for each item.
	* When setting one of the properties themself, a <None/_ui.ProgressBar> is expected.

	Custom iterable class containing the set of two possible progress bars:

	:type main: _ui.ProgressBar
	:param main: Main (global) progress bar.
	:type in_window: _ui.ProgressBar
	:param in_window: The bar in window.
	"""
	def __init__(self, main=None, in_window=None):
		super(ProgressBarsCouple, self).__init__()
		self.__main = None  # type: _ui.ProgressBar
		self.__in_window = None  # type: _ui.ProgressBar
		self.__both = tuple()  # type: Tuple[IsMainProgressBar]
		self.__n = 0
		self.__total = 0

		self.__set_main(main)
		self.__set_in_window(in_window)
		self.__update_both()

		self.__next__ = self.next


	def __update_both(self):
		"""
		Re-generate cached "both" tuple.
		"""
		self.__both = tuple(
			IsMainProgressBar(is_main, bar)
			for is_main, bar in ((True, self.__main), (False, self.__in_window))
			if not (bar is None)
		)

	def __set_main(self, val):
		"""
		:type val: _ui.ProgressBar
		"""
		self.__main = val or None

	def __set_in_window(self, val):
		"""
		:type val: _ui.ProgressBar
		"""
		self.__in_window = val or None

	@property
	def main(self):
		"""
		:rtype: None | _ui.ProgressBar
		"""
		return self.__main

	@main.setter
	def main(self, value):
		"""
		:type value: None | _ui.ProgressBar
		"""
		self.__set_main(value)
		self.__update_both()

	@property
	def in_window(self):
		"""
		:rtype: None | _ui.ProgressBar
		"""
		return self.__in_window

	@in_window.setter
	def in_window(self, value):
		"""
		:type value: None | _ui.ProgressBar
		"""
		self.__set_in_window(value)
		self.__update_both()

	def __iter__(self):
		self.__n = 0
		self.__total = len(self.__both)
		return self

	def next(self):
		"""
		:rtype: IsMainProgressBar
		"""
		n = self.__n
		if n < self.__total:
			bar = self.__both[n]
			self.__n = n + 1
			return bar
		else:
			raise StopIteration

	def iter_bars_only(self):
		"""
		Normally, this class is iterated as IsMainProgressBar.
		Using this method, you can generate the bars themselves.
		"""
		return (x.bar for x in self)

	def __len__(self):
		return len(self.__both)

	def __getitem__(self, item):
		"""
		:type item: int
		:rtype: None | _ui.ProgressBar
		"""
		return (self.__main, self.__in_window)[item]

	def __contains__(self, item):
		return item in self.__both

	def __get_str_repr(self, pattern, children_repr_f):
		"""
		:type pattern: str | unicode
		:rtype: str | unicode
		"""
		return pattern.format(
			n=self.__class__.__name__,
			id=hex(id(self)),
			m=children_repr_f(self.__main),
			w=children_repr_f(self.__in_window)
		)

	def __repr__(self):
		try:
			return self.__get_str_repr('<{n} {id}>: ({m}, {w})', repr)
		except UnicodeError:
			return self.__get_str_repr(u'<{n} {id}>: ({m}, {w})', repr)

	def __str__(self):
		return self.__get_str_repr('{n}({m}, {w})', str)

	def __unicode__(self):
		return self.__get_str_repr(u'{n}({m}, {w})', unicode)

# endregion


def _set_str_prop(set_f, val):
	"""
	Sets a property value in a unified way. I.e., ensures it's value is None/str/unicode.

	:type set_f: callable
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
		self.__p_bars = ProgressBarsCouple()
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
		Ensures there's a common private <__progresses_list> property and returns it value:
			* None: no window created yet
			* <pymel.core.uitypes.Window> The main multi-level progresses window.
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
		Tuple of **IsMainProgressBar** items
		the current progress is displayed in.
		"""
		return tuple(x for x in self.__p_bars)

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
		bar.setIsInterruptable(True)
		p_bars = self.__p_bars
		p_bars.main = bar
		self.__is_main = True
		map(self.__update_progress_bar, p_bars)

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
