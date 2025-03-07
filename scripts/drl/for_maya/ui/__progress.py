__author__ = 'Lex Darlog (DRL)'

try:
	# support type hints in Python 3:
	# noinspection PyUnresolvedReferences
	import typing as _t
except ImportError:
	pass

from pymel.core import (
	uitypes as ui,
	windows as _w,
)

from drl_py23 import (
	str_t as _str_t,
	str_h as _str_h,
	t_strict_unicode as _unicode,
)


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

	def __get_str_repr(
		self,
		pattern,  # type: _str_h
		children_repr_f,
	):
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
		return self.__get_str_repr(u'{n}({m}, {w})', _unicode)

# endregion


# region Functions for formatted template properties


def _prepare_template_prop(
	val,  # type: _str_h
	default,  # type: _str_h
):
	"""
	Error-checks property value before setting it. Ensures it's a string.
	"""
	if val and isinstance(val, _str_t):
		return val
	if not (default and isinstance(val, _str_t)):
		raise ProgressError(
			'Default value has to be a string. Got: {}'.format(repr(default))
		)
	return default


def _patterns_in_template(
	template,  # type: _str_h
	patterns,  # type: dict[_str_h, _t.Callable]
):
	"""
	Checks if the given template contains any of patterns for string formatting.

	:return: The dictionary of patterns present in the template.
	"""
	return {
		k: v for k, v in patterns.items()
		if ('{' + k) in template
	}


def _format_pattern(
	template,  # type: _str_h
	**kwargs
):
	try:
		return template.format(**kwargs)
	except UnicodeError:
		return _unicode(template).format(**kwargs)


def _get_kwargs(getters_dict):
	"""
	:type getters_dict: dict[str, () -> object]
	:rtype: dict[str, object]
	"""
	return {k: f() for k, f in getters_dict.items()}

# endregion


class Progress(object):
	def __init__(
		self,
		message_template='Progress [{cur}/{max}]',
		title_template='Progress: {percent}%',
		width=400, progresses_spacing=15, label_spacing=5, id=None,
		max_displayed=3, background=None
	):
		super(Progress, self).__init__()

		# Progress instance properties:
		self.__is_main = False
		self.__p_bars = ProgressBarsCouple()
		self.__max_displayed = 3
		self.__max_displayed = int(max_displayed)
		self.__width = int(width)
		self._width_can_change = False
		self.__id = None  # type: Optional[str]
		self.__set_id(id)  # can be here, since it doesn't depend on anything
		self.__progresses_spacing = int(progresses_spacing)
		self.__label_spacing = int(label_spacing)

		self.__layout_own = None  # type: Optional(ui.ColumnLayout)
		self.__label = None  # type: Optional(ui.Text)

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
		self.__message_patterns = self._format_patterns  # type: dict[str, _t.Callable[[], object]]
		self.__title_patterns = self._format_patterns  # type: dict[str, _t.Callable[[], object]]
		self._default_message_template = '{class} [{cur}/{max}]'
		self._default_title_template = '{class}: {percent}%'
		self.__message_changing = False
		self.__title_changing = False
		self.__message_template = ''
		self.__title_template = ''
		self.__get_message = lambda: self.__message_template
		self.__get_title = lambda: self.__title_template

		# Background:
		self.__background = None  # type: Optional[Tuple[Union(int, float)]]
		self._background_can_change = False

		# annotation-update chooser:
		self.__update_annotation = dict()  # type: dict[bool, Callable[[ui.ProgressBar]]]
		self.__update_annotation[True] = self.__update_status_in_main_bar
		self.__update_annotation[False] = self.__update_message_in_window

		self._update_progress = self._update_progress_bar

		# ensuring the class has the required common variables.
		# sic: Progress is called explicitly instead of self.__class__:
		# this way all the child classes will use the same common values,
		# unless explicitly overridden
		Progress.__get_progresses()
		Progress.__get_window()
		Progress.__get_layout_main()

		# after all the default values defined,
		# finally initialize it with the actual arguments:
		self.__set_message_template(message_template)
		self.__set_title_template(title_template)
		self.__set_background_with_check(background)


	# region Common class values

	@staticmethod
	def __get_layout_main():
		"""
		Ensures there's a common private <__layout_main> property and returns it's value:
			* None: no primary layout created yet
			* <ui.Window> The primary layout for the main multi-level progresses window.

		:rtype: ui.ColumnLayout | None
		"""
		try:
			return Progress.__layout_main
		except AttributeError:
			nu = None
			Progress.__layout_main = nu
			return nu

	@staticmethod
	def __set_layout_main(val):
		"""
		:type val: ui.ColumnLayout | None
		"""
		if not val:
			Progress.__layout_main = None
			return
		if not isinstance(val, ui.ColumnLayout):
			raise ProgressError(
				"Main layout should be <ui.ColumnLayout>. Got: {}".format(repr(val))
			)
		Progress.__layout_main = val


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

	@staticmethod
	def __set_window(val):
		"""
		:type val: ui.Window | None
		"""
		if not val:
			Progress.__window_obj = None
			return
		if not isinstance(val, ui.Window):
			raise ProgressError(
				"Internal window should be <ui.Window>. Got: {}".format(repr(val))
			)
		Progress.__window_obj = val

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
		and returns it's value.

		:rtype: list[Progress]
		"""
		try:
			return Progress.__progresses_list
		except AttributeError:
			nu = []
			Progress.__progresses_list = nu
			return nu

	@staticmethod
	def __set_progresses(val):
		"""
		:type val: list[Progress]
		"""
		if not val:
			Progress.__progresses_list = []
		Progress.__progresses_list = val

	@property
	def progresses(self):
		return tuple(Progress.__get_progresses())  # type: Tuple[Progress]

	def _get_main_progress_or_this(self, attach_this=True):
		"""
		Service getter-method, which guarantees you get a proper Progress object.
		Either a main Progress (if the overall progresses list is not empty),
		or the current one.

		:type attach_this: bool
		:param attach_this:
			If True, the current Progress is guaranteed to be added to the progresses lest.
			So, it could become a main progress if there was none.

			Otherwise, the function may return self, but it won't be added to the list.
		:rtype: Progress
		"""
		progresses = Progress.__get_progresses()
		if not(self in progresses) and attach_this:
			progresses.append(self)
		if progresses:
			return progresses[0]
		return self


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
		(possible) Couple of progress-bars the current progress is displayed in.
		"""
		bars = self.__p_bars
		return ProgressBarsCouple(main=bars.main, in_window=bars.in_window)

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

	@property
	def progresses_spacing(self):
		"""
		The distance (in pixels) between different progresses, in the window.

		This setting is used only if the current progress is main.
		"""
		return self.__progresses_spacing

	@property
	def label_spacing(self):
		"""
		The distance (in pixels) between a progress and it's label, in the window.

		This setting is used only if the current progress is main.
		"""
		return self.__label_spacing

	@property
	def _layout(self):
		"""
		The ColumnLayout of the current progress-bar, contained by the
		main Window layout.

		:rtype: ui.ColumnLayout | None
		"""
		return self.__layout_own

	@_layout.setter
	def _layout(self, value):
		"""
		:type value: ui.ColumnLayout | None
		"""
		if not value:
			self.__layout_own = None
		if not isinstance(value, ui.ColumnLayout):
			raise ProgressError(
				"Progress' layout should be <ui.ColumnLayout>. Got: {}".format(repr(value))
			)
		self.__layout_own = value

	@property
	def _label(self):
		"""
		:rtype: ui.Text | None
		"""
		return self.__label

	@_label.setter
	def _label(self, value):
		"""
		:type value: ui.Text | None
		"""
		if not value:
			self.__label = None
		if not isinstance(value, ui.Text):
			raise ProgressError(
				"Progress' label should be <ui.Text>. Got: {}".format(repr(value))
			)
		self.__label = value

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
	def id(self):
		"""
		The ID of this progress that's used for the window internal name.
			* if specified, the window's ID will be '{class name}_{id}'
			* otherwise, it will be just "{class name}".

		The property is read-only and is specified only at initialisation time.

		:rtype: str | None
		"""
		return self.__id

	def window_id(self):
		"""
		Generates the internal name (aka id) of the progress window.
		It has to be ASCII-compliant, so use only alphanumeric characters and underscores.
			* if **id** property is specified, the window's ID will be: '{class name}_{id}'
			* otherwise, it will be just "{class name}".

		The generated name corresponds to self, not to the main progress bar.

		It's automatically used to create main window and for each progress' UI elements.

		:rtype: str
		"""
		return '_'.join(
			filter(None, (self.__class__.__name__, self.id))
		)

	@property
	def formatting_patterns(self):
		"""
		The tuple of possible patterns for message/title string formatting.
		Each patter should be used as regular formatting in string.

		I.e.: '{pattern}'.

		:rtype: tuple[str]
		"""
		return tuple(sorted(
			self._format_patterns.keys()
		))

	# endregion


	# region property setters

	def __set_message_template(
		self,
		val,  # type: _t.Optional[_str_h]
	):
		"""
		Setter for **message template**. It also sets up the proper getter.

		I.e., the message formatting is performed only if
		the template contains any of the replacement patterns.
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

	def __set_title_template(
		self,
		val,  # type: _t.Optional[_str_h]
	):
		"""
		Setter for **title template**. It also sets up the proper getter.

		I.e., the message formatting is performed only if
		the template contains any of the replacement patterns.
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
		Sets background property value, but doesn't update it in UI.

		:type val: tuple[int | float] | int | float | None
		"""
		if val is None:
			self.__background = None
			return
		if isinstance(val, (int, float)):
			val = (val,) * 3
		self.__background = tuple(val)

	def __set_id(self, val):
		"""
		:type val: str | None
		"""
		if not val:
			self.__id = None
			return
		if isinstance(val, str):
			self.__id = val

		self.__id = str(val)

	# endregion

	# region Writeable properties

	@property
	def width(self):
		"""
		Width of the progress-window, **if this progress is main**.

		Otherwise, the width is taken from the corresponding main progress' property.

		:rtype: int
		"""
		return self.__width

	@width.setter
	def width(self, value):
		value = int(value)
		self.__width = value
		self._update_window_width()



	@property
	def message_template(self):
		return self.__message_template

	@message_template.setter
	def message_template(
		self,
		value,  # type: _t.Optional[_str_h]
	):
		"""
		When **None** is provided, the template is reset to the default one.
		"""
		self.__set_message_template(value)
		self._gen_update_f()
		for is_main, bar in self.bars:
			self._update_message(is_main, bar)

	def message(self):
		"""
		Generate formatted progress message.
		"""
		return self.__get_message()



	@property
	def title_template(self):
		return self.__title_template

	@title_template.setter
	def title_template(
		self,
		value,  # type: _t.Optional[_str_h]
	):
		"""
		When **None** is provided, the template is reset to the default one.
		"""
		self.__set_title_template(value)
		self._gen_update_f()
		for is_main, bar in self.bars:
			self._update_title(is_main)

	def title(self):
		"""
		Generate formatted window title with the template from the current Progress.
		"""
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
		self._update_background()

	# endregion

	# region Update individual UI components methods

	def _update_background(self):
		"""
		If current Progress' layout is present, update it's background.

		It's called automatically from:
			* background property setter
			* progress-bar initializer
			*
				if background is set to changeable in child class,
				it's also updated at each progress change

		But you may also need to call it manually from child classes, in special cases.
		"""
		layout = self._layout
		if not layout:
			return

		bg = self.background
		if bg is None:
			layout.noBackground(True)
			return
		layout.setEnableBackground(True)
		layout.setBackgroundColor(bg)

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

	def __update_message_in_window(self, bar):
		"""
		Just a one-case function, with no check. Instead of this, use:

		self.__update_annotation[is_main]

		It updates message and annotation for in-window progress bar, layout and label.

		:type bar: ui.ProgressBar
		"""
		message = self.message()
		label = self._label
		updated_items = (x for x in (bar, self._layout, label) if x)
		for ui_element in updated_items:
			ui_element.setAnnotation(message)
		if label:
			label.setLabel(message)

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

		window = self.window
		if not isinstance(window, ui.Window):
			raise ProgressError(
				'Trying to modify a non-existent window. '
				'<ui.Window> expected. Got: {}'.format(repr(window))
			)
		window.setTitle(self.title())

	def _update_window_width(self):
		"""
		Recursively updates the active progress-window and all of it's contents.

		Takes the width from the main progress, not from the current one.
		"""
		width = self._get_main_progress_or_this(attach_this=False).width  # type: int

		updated_items = [  # some items may be None, they're filtered out later
			self.window,
			self.__get_layout_main()
		]
		extend = updated_items.extend
		for p in self.__get_progresses():
			extend([p._layout, p._label, p.bars.in_window])

		for item in filter(None, updated_items):
			item.setWidth(width)

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
			(  # min:
				lambda: self._min_can_change,
				lambda is_main, bar: self._update_min(bar)
			),
			(  # max:
				lambda: self._max_can_change,
				lambda is_main, bar: self._update_max(bar)
			),
			(  # current:
				lambda: self._cur_can_change,
				lambda is_main, bar: self._update_current(bar)
			),
			(  # title:
				lambda: self.__title_changing,
				lambda is_main, bar: self._update_title(is_main)
			),
			(  # message:
				lambda: self.__message_changing,
				self._update_message
			),
			(  # background:
				lambda: self._background_can_change,
				lambda is_main, bar: self._update_background()
			),
			(  # window width:
				lambda: self._width_can_change,
				lambda is_main, bar: self._update_window_width()
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

	# TODO: un-setup main progress bar

	def __setup_main_progress_bar(self):
		bar = _w.getMainProgressBar()
		bar.setIsInterruptable(True)
		p_bars = self.__p_bars
		p_bars.main = bar
		self.__is_main = True
		self._gen_update_f()
		map(self._update_progress_bar, p_bars)

	# TODO: auto-setup any UI for self

	def __remove_progress_from_window(self):
		for ui_cmd, el in (
			(_w.progressBar, self.__p_bars.in_window),
			(_w.text, self._label),
			(_w.layout, self._layout)
		):
			if el and ui_cmd(el, q=1, ex=1):
				el.delete()

		self.__p_bars.in_window = None
		self._label = None
		self._layout = None

	def __attach_progress_to_window(self):
		self.__remove_progress_from_window()
		main_layout = self.__get_layout_main()
		if not main_layout:
			raise ProgressError(
				"Can't create progress {pr} because no main layout created. "
				"Expected (as parent layout): <ui.ColumnLayout>. Got: {layout}".format(
					pr=repr(self), layout=main_layout
				)
			)

		# get required common data:
		main_progress = self._get_main_progress_or_this(attach_this=True)
		width = main_progress.width
		progress_id = self.window_id()
		message = self.message()

		layout = _w.columnLayout(
			'pl_' + progress_id,
			parent=main_layout,
			adjustableColumn=1,  # snap both ends of children to column
			columnAlign='left',
			rowSpacing=main_progress.label_spacing,
			columnWidth=width,
			width=width
		)
		self._layout = layout

		self._label = _w.text(
			'lbl_' + progress_id,
			parent=layout,
			annotation=message,
			label=message,
			wordWrap=1,
			recomputeSize=1,
			width=width
		)

		bar = _w.progressBar(
			'bar_' + progress_id,
			parent=layout,
			annotation=message,
			min=self.min,
			max=self.max,
			progress=self.current,
			width=width
		)
		self.__p_bars.in_window = bar

		self._gen_update_f()
		self._update_progress_bar(IsMainProgressBar(is_main=False, bar=bar))


	@staticmethod
	def __delete_main_layout():
		for pr in reversed(Progress.__get_progresses()):
			pr.__remove_progress_from_window()
		layout = Progress.__get_layout_main()
		if not(layout and _w.layout(layout, q=1, ex=1)):
			return

		layout.delete()
		Progress.__set_layout_main(None)

	@staticmethod
	def __generate_main_layout():
		w = Progress.__get_window()
		if not w:
			raise ProgressError(
				"Layout name can be generated only with a proper window specified. "
				"Expected: <ui.Window>. Got: {}".format(repr(w))
			)

		progresses = Progress.__get_progresses()
		if not progresses:
			raise ProgressError(
				"Can't generate a main window layout since there's no main progress yet. "
				"Expected: list[Progress]. Got: {}".format(repr(progresses))
			)

		if Progress.__get_layout_main():
			Progress.__delete_main_layout()

		main_progress = progresses[0]
		width = main_progress.width

		layout = _w.columnLayout(
			'L_' + w.shortName(),
			parent=w,
			adjustableColumn=1,  # snap both ends of children to column
			columnAlign='left',
			rowSpacing=main_progress.progresses_spacing,
			columnWidth=width,
			width=width
		)
		Progress.__set_layout_main(layout)
		for pr in progresses:
			pr.__attach_progress_to_window()
		main_progress._update_window_width()

	@staticmethod
	def __delete_window():
		Progress.__delete_main_layout()
		w = Progress.__get_window()
		if not(w and _w.window(w, q=1, ex=1)):
			return

		w.delete()
		Progress.__set_window(None)

	def __generate_window(self):
		Progress.__delete_window()
		main_progress = self._get_main_progress_or_this(attach_this=True)

		w = _w.window(
			main_progress.window_id(),
			maximizeButton=0,
			minimizeButton=0,
			resizeToFitChildren=1,
			sizeable=0,  # disables the window resize by user, still possible via script
			# iconify=1,  # minimize window
			titleBarMenu=0,  # 0: also disables 'cross' button
			# titleBar=0,
			title=main_progress.title(),
			# visible=1,
			# height=100,
			width=main_progress.width
		)
		self.__set_window(w)
		self.__generate_main_layout()
		w.show()

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
		pr = self.__get_progresses()
		if not(self in pr):
			self.__interrupt()
			return

		i = pr.index(self)
		removed = pr[i:]  # all the preceding progresses before current
		left = pr[:i]  # current progress and all the rest
		for p in removed:
			p.__interrupt()
		self.__set_progresses(left)

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
