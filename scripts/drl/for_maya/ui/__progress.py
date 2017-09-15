__author__ = 'DRL'

from itertools import izip
from functools import partial

from pymel.core import (
	uitypes as ui,
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
			('bar', ui.ProgressBar),
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
	*
		When setting one of the properties themselves,
		a <None/ui.ProgressBar> is expected.

	Custom iterable class containing the set of two possible progress bars:

	:type main: ui.ProgressBar
	:param main: Main (global) progress bar.
	:type in_window: ui.ProgressBar
	:param in_window: The bar in window.
	"""
	def __init__(self, main=None, in_window=None):
		super(ProgressBarsCouple, self).__init__()
		self.__main = None  # type: ui.ProgressBar
		self.__in_window = None  # type: ui.ProgressBar
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
		:type val: ui.ProgressBar
		"""
		self.__main = val or None

	def __set_in_window(self, val):
		"""
		:type val: ui.ProgressBar
		"""
		self.__in_window = val or None

	@property
	def main(self):
		"""
		:rtype: None | ui.ProgressBar
		"""
		return self.__main

	@main.setter
	def main(self, value):
		"""
		:type value: None | ui.ProgressBar
		"""
		self.__set_main(value)
		self.__update_both()

	@property
	def in_window(self):
		"""
		:rtype: None | ui.ProgressBar
		"""
		return self.__in_window

	@in_window.setter
	def in_window(self, value):
		"""
		:type value: None | ui.ProgressBar
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
		:rtype: None | ui.ProgressBar
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


# region Functions for formatted template properties


def _prepare_template_prop(val, default):
	"""
	Error-checks property value before setting it. Ensures it's a string.

	:type val: str | unicode | None
	:type default: str | unicode
	"""
	if val and isinstance(val, _str_t):
		return val
	if not (default and isinstance(val, _str_t)):
		raise ProgressError(
			'Default value has to be a string. Got: {}'.format(repr(default))
		)
	return default


def _patterns_in_template(template, patterns):
	"""
	Checks if the given template contains any of patterns for string formatting.

	:type template: str | unicode
	:type patterns: dict[str, () -> object]
	:rtype: dict[str, () -> object]
	:return: The dictionary of patterns present in the template.
	"""
	return {
		k: v for k, v in patterns.iteritems()
		if ('{' + k) in template
	}


def _format_pattern(template, **kwargs):
	"""
	:type template: str | unicode
	:type kwargs: dict[str, object]
	:rtype: str | unicode
	"""
	try:
		return template.format(**kwargs)
	except UnicodeError:
		return unicode(template).format(**kwargs)


def _get_kwargs(getters_dict):
	"""
	:type getters_dict: dict[str, () -> object]
	:rtype: dict[str, object]
	"""
	return {k: f() for k, f in getters_dict.iteritems()}

# endregion


class Progress(object):
	def __init__(
		self,
		message_template='Progress [{cur}/{max}]',
		title_template='Progress: {percent}%',
		max_displayed=3, background=None
	):
		super(Progress, self).__init__()

		# Progress instance properties:
		self.__is_main = False
		self.__p_bars = ProgressBarsCouple()
		self.__max_displayed = 3
		self.__max_displayed = int(max_displayed)

		# ProgressBar UI read-only properties:
		self.__min_value = 0  # type: Union(int, float)
		self.__max_value = 100  # type: Union(int, float)
		self.__cur_value = 0  # type: Union(int, float)
		self._min_can_change = False
		self._max_can_change = False
		self._cur_can_change = True

		# message properties (for formatting):
		self._format_patterns = {  # could be overridden in child classes
			'cur': lambda: self.__cur_value,
			'min': lambda: self.__min_value,
			'max': lambda: self.__max_value,
			'percent': lambda: format(
				100.0 * (self.__cur_value - self.__min_value) / self.__max_value,
				'.2f'
			),
			'class': lambda: self.__class__.__name__
		}
		self.__message_patterns = self._format_patterns  # type: Dict[str, () -> object]
		self.__title_patterns = self._format_patterns  # type: Dict[str, () -> object]
		self._default_message_template = '{class} [{cur}/{max}]'
		self._default_title_template = '{class}: {percent}%'
		self.__message_changing = False
		self.__title_changing = False
		self.__message_template = ''
		self.__title_template = ''
		self.__get_message = lambda: self.__message_template
		self.__get_title = lambda: self.__title_template

		# Background:
		self.__background = None  # type: Tuple[Union(int, float)]
		self._background_can_change = False

		# annotation-update chooser:
		self.__update_annotation = dict()  # type: Dict[bool, Callable[[ui.ProgressBar]]]
		self.__update_annotation[True] = self.__update_status_in_main_bar
		self.__update_annotation[False] = self.__update_annotation_in_window

		self._update_progress = self._update_progress_bar

		# ensuring the class has the required common variables.
		# sic: Progress is called explicitly instead of self.__class__:
		# this way all the child classes will use the same common values,
		# unless explicitly overridden
		Progress.__get_progresses()
		Progress.__get_window()

		# after all the default values defined,
		# finally initialize it with the actual arguments:
		self.__set_message_template(message_template)
		self.__set_title_template(title_template)
		self.__set_background_with_check(background)


	# region Common class values

	@staticmethod
	def __get_window():
		"""
		Ensures there's a common private <__window> property and returns it's value:
			* None: no window created yet
			* <ui.Window> The main multi-level progresses window.

		:rtype: ui.Window | None
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
		"""
		:type value: ui.Window
		"""
		Progress.__window_obj = value

	@property
	def window(self):
		"""
		:rtype: ui.Window | None
		"""
		return Progress.__get_window()

	@staticmethod
	def __get_progresses():
		"""
		Ensures there's a common private <__progresses_list> property
		and returns it value.

		:rtype: list[Progress]
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
		"""
		:type value: list[Progress]
		"""
		Progress.__progresses_list = value

	@property
	def progresses(self):
		return tuple(Progress.__get_progresses())  # type: Tuple[Progress]

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
		Tuple of progress-bars the current progress is displayed in.
		"""
		return tuple(x for x in self.__p_bars)

	@property
	def max_displayed(self):
		"""
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
		self.__max_displayed = int(value)

	# endregion

	# region read-only UI properties

	@property
	def min(self):
		"""
		:rtype: int | float
		"""
		return self.__min_value

	@property
	def max(self):
		"""
		:rtype: int | float
		"""
		return self.__max_value

	@property
	def current(self):
		"""
		:rtype: int | float
		"""
		return self.__cur_value

	@property
	def formatting_patterns(self):
		"""
		The tuple of possible patterns for message/title string formatting.
		Each patter should be used as regular formatting in string.

		I.e.: '{pattern}'.

		:rtype: tuple[str]
		"""
		return tuple(sorted(
			self._format_patterns.iterkeys()
		))

	# endregion


	# region Writeable property setters

	def __set_message_template(self, val):
		"""
		Setter for **message template**. It also sets up the proper getter.

		I.e., the message formatting is performed only if
		the template contains any of the replacement patterns.

		:type val: str | unicode | None
		"""
		template = _prepare_template_prop(val, self._default_message_template)
		self.__message_template = template
		contained_patterns = _patterns_in_template(template, self._format_patterns)

		if contained_patterns:
			self.__message_patterns = contained_patterns
			self.__get_message = lambda: _format_pattern(
				self.__message_template,
				**_get_kwargs(self.__message_patterns)
			)
			self.__message_changing = True
		else:
			self.__message_patterns = {}
			self.__get_message = lambda: self.__message_template
			self.__message_changing = False

	def __set_title_template(self, val):
		"""
		Setter for **title template**. It also sets up the proper getter.

		I.e., the message formatting is performed only if
		the template contains any of the replacement patterns.

		:type val: str | unicode | None
		"""
		template = _prepare_template_prop(val, self._default_title_template)
		self.__title_template = template
		contained_patterns = _patterns_in_template(template, self._format_patterns)

		if contained_patterns:
			self.__title_patterns = contained_patterns
			self.__get_title = lambda: _format_pattern(
				self.__title_template,
				**_get_kwargs(self.__title_patterns)
			)
			self.__title_changing = True
		else:
			self.__title_patterns = {}
			self.__get_title = lambda: self.__title_template
			self.__title_changing = False

	def __set_background_with_check(self, val):
		"""
		:type val: tuple[int | float] | int | float | None
		"""
		def _set(v):
			if v is None:
				self.__background = None
				return
			if isinstance(v, (int, float)):
				v = (v,) * 3
			self.__background = tuple(v)

		_set(val)

		bars_in_window = tuple(
			bar for is_main, bar in self.bars
			if not is_main
		)
		map(
			partial(self._update_background, is_main=False),
			bars_in_window
		)

	# endregion

	# region Writeable properties

	@property
	def message_template(self):
		return self.__message_template

	@message_template.setter
	def message_template(self, value):
		"""
		When **None** is provided, the template is reset to the default one.

		:type value: str | unicode | None
		"""
		self.__set_message_template(value)
		self._gen_update_f()
		for is_main, bar in self.bars:
			self._update_message(is_main, bar)

	def message(self):
		return self.__get_message()



	@property
	def title_template(self):
		return self.__title_template

	@title_template.setter
	def title_template(self, value):
		"""
		When **None** is provided, the template is reset to the default one.

		:type value: str | unicode | None
		"""
		self.__set_title_template(value)
		self._gen_update_f()
		for is_main, bar in self.bars:
			self._update_title(is_main)

	def title(self):
		return self.__get_title()



	@property
	def background(self):
		"""
		:rtype: tuple[int|float] | None
		"""
		return self.__background

	@background.setter
	def background(self, value):
		"""
		:type value: tuple[int|float] | int | float | None
		"""
		self.__set_background_with_check(value)
		for is_main, bar in self.bars:
			self._update_background(is_main, bar)

	# endregion

	# region Update individual UI components methods

	def _update_background(self, is_main, bar):
		"""
		:type is_main: bool
		:type bar: ui.ProgressBar
		"""
		if is_main:
			return

		bg = self.background
		if bg is None:
			bar.noBackground()
			return
		bar.setEnableBackground()
		bar.setBackgroundColor(bg)

	def _update_min(self, bar):
		"""
		:type bar: ui.ProgressBar
		"""
		bar.setMinValue(self.min)

	def _update_max(self, bar):
		"""
		:type bar: ui.ProgressBar
		"""
		bar.setMaxValue(self.max)

	def _update_current(self, bar):
		"""
		:type bar: ui.ProgressBar
		"""
		bar.setProgress(self.current)

	def __update_annotation_in_window(self, bar):
		"""
		Just a one-case function, with no check. Instead of this, use:

		self.__update_annotation[is_main]

		:type bar: ui.ProgressBar
		"""
		bar.setAnnotation(self.message())

	def __update_status_in_main_bar(self, bar):
		"""
		Just a one-case function, with no check. Instead of this, use:

		self.__update_annotation[is_main]

		:type bar: ui.ProgressBar
		"""
		bar.setStatus(self.message())

	def _update_message(self, is_main, bar):
		"""
		:type is_main: bool
		:type bar: ui.ProgressBar
		"""
		self.__update_annotation[bool(is_main)](bar)

	def _update_title(self, is_main_bar):
		"""
		:type is_main_bar: bool
		"""
		if is_main_bar:
			return

		window = self.__get_window()
		if not isinstance(window, ui.Window):
			raise ProgressError(
				'Trying to modify a non-existent window. '
				'<ui.Window> expected. Got: {}'.format(repr(window))
			)
		window.setTitle(self.title())

	# endregion

	# region Update the entire ProgressBar UI

	def _all_update_functions(self):
		"""
		This method should be overridden by child classes,
		adding all the extra UI-update methods.
		It returns a tuple containing tuples of two functions:

			*
				() -> bool:

				Called only once, during the **update function** generation.
				It specifies whether the 2nd function should be called
				when updating UI during progress.
			*
				(is_main: bool, bar: ui.ProgressBar) -> None:

				It's called to actually update the UI.

		:rtype: tuple[tuple[() -> bool, (bool, ui.ProgressBar) -> None]]
		"""
		return (
			(
				lambda: self._min_can_change,
				lambda is_main, bar: self._update_min(bar)
			),
			(
				lambda: self._max_can_change,
				lambda is_main, bar: self._update_max(bar)
			),
			(
				lambda: self._cur_can_change,
				lambda is_main, bar: self._update_current(bar)
			),
			(
				lambda: self.__title_changing,
				lambda is_main, bar: self._update_title(is_main)
			),
			(
				lambda: self.__message_changing,
				self._update_message
			),
			(
				lambda: self._background_can_change,
				self._update_background
			)
		)

	def _gen_update_f(self):
		"""
		This method re-generates the function used to update the Progress-Bar.

		This function is called internally on each IsMainProgressBar
		at each progress increment.
		"""
		funcs = [  # type: List[Callable[[bool, ui.ProgressBar]]]
			f for changing, f in self._all_update_functions() if changing()
		]

		def update(p_bar):
			"""
			:type p_bar: IsMainProgressBar
			"""
			is_main, bar = p_bar
			for func in funcs:
				func(is_main, bar)

		self._update_progress = update
		# TODO: use it ^

	def _update_progress_bar(self, p_bar):
		"""
		This method updates ALL the ProgressBar UI properties.

		:type p_bar: IsMainProgressBar
		"""
		funcs = (f for changing, f in self._all_update_functions())
		is_main, bar = p_bar
		for func in funcs:
			func(is_main, bar)

	# TODO: set/update window properties (height, width)

	# endregion

	# region Generate UI

	def __setup_main_progress_bar(self):
		bar = _w.getMainProgressBar()
		bar.setIsInterruptable(True)
		p_bars = self.__p_bars
		p_bars.main = bar
		self.__is_main = True
		map(self._update_progress_bar, p_bars)

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
