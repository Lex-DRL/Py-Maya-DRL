__author__ = 'Lex Darlog (DRL)'

from drl_common.is_maya import is_maya

__maya = is_maya()
if __maya:
	from maya import cmds

from . import confirm_icon, confirm_align, file_mode
from drl_common import (
	errors as err,
	filesystem as fs,
)
from drl_common.py_2_3 import (
	str_t as _str_t,
	str_h as _str_h,
	t_strict_str as _str,
	t_strict_unicode as _unicode,
)


class Button(object):
	def __init__(self, title, annotation=None):
		super(Button, self).__init__()
		self.__title = ''
		self.__annotation = ''
		self.set_title(title)
		self.set_annotation(annotation)

	def set_title(self, val):
		self.__title = err.NotStringError(val, 'title').raise_if_needed_or_empty()
		return self

	def set_annotation(self, val):
		if val is None:
			val = ''
		self.__annotation = err.NotStringError(val, 'annotation').raise_if_needed()
		return self

	@property
	def title(self):
		return self.__title

	@title.setter
	def title(self, value):
		self.set_title(value)

	@property
	def annotation(self):
		return self.__annotation

	@annotation.setter
	def annotation(self, value):
		self.set_annotation(value)

	@staticmethod
	def cleanup_button_argument(button, button_name):
		"""
		Performs error-check for an argument expected to be a Button.

		If string or list/tuple of strings (with lengh of 1/2) is provided,
		the proper Button instance is returned instead of error.

		:param button: <Button/string/list/tuple> - the value of the button argument.
		:param button_name: the name of this argument (for proper errors, if any).
		:return: <Button>
		:raises:
		* EmptyStringError
		* WrongTypeError
		"""
		if not button:
			raise err.EmptyStringError(button_name)

		if isinstance(button, _str_t):
			return Button(button)
		if isinstance(button, (tuple, list)):
			return Button(
				button[0],
				button[1] if (len(button) > 1) else None
			)

		return err.WrongTypeError(
			button, Button, button_name, 'Button class, string or list/tuple'
		).raise_if_needed()


def confirm(
	title='Confirmation',
	message='Are you sure?', message_align=None,
	yes=Button('Yes', 'Perform the operation'), no=Button('No', 'Cancel'),
	extra_buttons=None,
	icon=None, background_color=None,
	parent_window=None,
	default_if_not_maya=1
):
	"""
	A high-level wrapper for cmds.confirmDialog().
	Basically, all it does is:

	* it's safe to use if we're calling this dialog not from Maya;
	* performs some error-checks for input arguments;
	* provides enum-style <confirm_icon> and <confirm_align> submodules;
	* works with more convenient <Button> class instead of lists of strings.

	:param title: <str, REQUIRED> The title of the window
	:param message: <str, REQUIRED> The confirmation message (question) shown in the dialog.
	:param message_align: <str, optional> Message alignment. Use <confirm_align> as enum for available values.
	:param yes: <REQUIRED> The first button, which acts as 'yes' user input. You can pass one of:

		* <Button> class instance. It has both title and annotation.
		* <str> - button name with no annotation.
		* <2 strings as list/tuple> - title, annotation.
	:param no: <REQUIRED> Similarly, the last button, acting as 'no' user input. If user press Esc, it's also considered as 'no'.
	:param extra_buttons: <list/tuple/string, optional> Additional buttons that will be inserted between 'yes' and 'no'.

		* None: no extra buttons
		* string: one button, only name, without annotation. If you need annotation, you have to use the next option.
		* list/tuple: list of multiple buttons, each of which could have the same value as <yes> argument.
	:param icon: <str, optional> The big icon displayed on the left from the message text. Use confirm_icon as enum for available values.
	:param background_color: <float/int/ 3-tuple of floats> The background color of the dialog. The arguments correspond to the red, green, and blue color components. Each component ranges in value from 0.0 to 1.0. (Windows only flag)
	:param parent_window: <string, optional> The parent window for the dialog. The dialog will be centered on this window and raise and lower with it's parent. By default, the dialog is not parented to a particular window and is simply centered on the screen.
	:param default_if_not_maya: <int/bool, optional> This is the value returned when this function is called not from maya (so no dialog box can be created).
	:return: user choice as int:

		* 0 - No
		* 1 - yes
		* 2 and more - the corresponding extra button.
			(2: extra1, 3: extra2, ...)
	"""
	if not __maya:
		return default_if_not_maya

	kw_args = dict()

	# main window arguments: parent, title, message, icon:
	title = err.NotStringError(title, 'title').raise_if_needed_or_empty()
	message = err.NotStringError(message, 'message').raise_if_needed_or_empty()
	if parent_window:
		kw_args['parent_window'] = err.NotStringError(parent_window, 'parent_window').raise_if_needed()
	if message_align:
		kw_args['messageAlign'] = err.NotStringError(message_align, 'message_align').raise_if_needed_or_empty()
	if icon and isinstance(icon, _str_t):
		kw_args['icon'] = icon

	# color:
	def _append_color():
		if background_color is None:
			return

		if isinstance(background_color, (int, float)):
			kw_args['backgroundColor'] = (background_color,) * 3
			return

		kw_args['backgroundColor'] = err.WrongTypeError(
			background_color,
			(list, tuple),
			'background_color'
		).raise_if_needed()

	_append_color()

	# yes/no buttons (cleanup):
	yes = Button.cleanup_button_argument(yes, 'yes')
	title_yes = yes.title
	no = Button.cleanup_button_argument(no, 'no')
	title_no = no.title

	def _error_check_extra_buttons():
		"""
		Add extra buttons to the full list, if any.
		"""
		if not extra_buttons:
			return []

		if isinstance(extra_buttons, (list, tuple)):
			return [Button.cleanup_button_argument(b, 'extra_button') for b in extra_buttons]
		if isinstance(extra_buttons, Button):
			return [extra_buttons]
		if isinstance(extra_buttons, _str_t):
			return [Button.cleanup_button_argument(extra_buttons, 'extra_buttons')]
		raise err.WrongTypeError(
			extra_buttons,
			(Button, list, tuple, _str, _unicode),
			'extra_buttons',
			'list or tuple of Buttons / Button / string'
		)

	# combine all buttons to a list:
	all_buttons = list()
	extra_indices = dict()
	extra_buttons = _error_check_extra_buttons()
	for i, e in enumerate(extra_buttons):
		assert isinstance(e, Button)
		extra_indices[e.title] = i

	all_buttons.append(yes)
	all_buttons.extend(extra_buttons)
	all_buttons.append(no)

	button_titles = list()
	annotations = list()
	for i, b in enumerate(all_buttons):
		assert isinstance(b, Button)
		name = b.title
		button_titles.append(name)
		annotations.append(b.annotation)

	if any(annotations):
		kw_args['annotation'] = annotations

	# finally, let's show a popup dialog:

	user_choice = cmds.confirmDialog(
		title=title,
		message=message,
		button=button_titles,
		defaultButton=title_yes,
		cancelButton=title_no,
		dismissString=title_no,
		**kw_args
	)

	if user_choice == title_yes:
		return 1
	if user_choice == title_no:
		return 0
	return extra_indices[user_choice] + 2


def file_chooser(
	title=None,
	mode=file_mode.FILE_ANY,
	ok=None, cancel=None,
	file_filters=None, default_filter=0, return_filter=False,
	starting_directory=None,
	os_dialog=False,
	default_if_not_maya=None
):
	"""
	A high-level wrapper for cmds.fileDialog2.
	Basically, all it does is:

	* it's safe to use if we're calling this dialog not from Maya;
	* performs some error-checks for input arguments;
	* provides enum-style <file_mode> submodule;
	* works with more convenient <FileFilter> class from drl_common.filesystem module.

	:param title: <str> The file-chooser window title.
	:param mode: <int>, whether this dialog chooses file or folder. Use <file_mode> submodule values.
	:param ok: <string> custom text for "OK" button.
	:param cancel: <string> custom text for "Cancel" button.
	:param file_filters: The available file filters. You can define it either way:

		* fs.FileFilter or list/tuple of them - the most flexible variant.
		* None/empty value - Single default "All files" filter
		* string - Single default "All files" filter, with custom name
		* list/tuple of strings - single filter, the 1st item is filter name, the rest (optional) items are file masks.
		* list/tuple of multiple file filters. Their items are (in any combination):
			* None/empty
			* lists/tuples of strings
			* fs.FileFilter instances
	:param default_filter: <int> 0-based index of the file filter selected by default.
	:param return_filter: <bool> when True, 2 values are returned. The 2nd one is the file filter used
	:param starting_directory: <string> when specified, the path of a folder opened in the dialog by default. If omited, the current working directory is used.
	:param os_dialog: <bool> When True, for Windows and Mac OS X the default system file navigator will be used.
	:param default_if_not_maya: <string/None> This is the value returned when this function is called not from maya (so no dialog box can be created).
	:return: <None / string / list / 2-elements tuple>:

		* if return_filter is True, two elements are returned:
			* user choice (see below),
			* <fs.FileFilter> selected by user
		* otherwise, only user choice is returned. Which is:
			* <list of strings> if <modes> is file_mode.FILES_MULTIPLE
			* single <string> in any other mode.
	"""
	if not __maya:
		return default_if_not_maya

	def _error_check_file_filters(filters):
		if (
			isinstance(filters, (list, tuple)) and
			not fs.FileFilter.error_check_condition(3)(filters)
		):
			filters = [
				fs.FileFilter.error_check_as_argument(x, 'file_filter #' + str(i))
				for i, x in enumerate(filters)
			]
		else:
			filters = [fs.FileFilter.error_check_as_argument(filters, 'file_filters')]

		if isinstance(filters, list):
			from pprint import pprint as pp
			pp(filters)
			filters = tuple(filters)

		return err.WrongTypeError(filters, tuple, 'filters').raise_if_needed()

	default_filter = err.WrongTypeError(default_filter, int, 'default_filter').raise_if_needed()
	mode = err.WrongTypeError(mode, int, 'mode').raise_if_needed()

	kw_args = dict()
	if starting_directory:
		kw_args['startingDirectory'] = err.NotStringError(
			starting_directory, 'starting_directory'
		).raise_if_needed()
	if title:
		kw_args['caption'] = err.NotStringError(title, 'title').raise_if_needed()
	if ok:
		kw_args['okCaption'] = err.NotStringError(ok, 'ok').raise_if_needed()
	if cancel:
		kw_args['cancelCaption'] = err.NotStringError(cancel, 'cancel').raise_if_needed()
	if return_filter:
		kw_args['returnFilter'] = True
	file_filters = _error_check_file_filters(file_filters)
	file_filters_str = tuple([str(x) for x in file_filters])

	style = 1 if os_dialog else 2
	choice = cmds.fileDialog2(
		dialogStyle=style,
		fileFilter=';;'.join(file_filters_str),
		selectFileFilter=file_filters[default_filter].name,
		fileMode=mode,
		**kw_args
	)

	if choice is None:
		return None

	if return_filter:
		assert isinstance(choice, list)
		used_filter = choice.pop()
		used_filter = [x.name for x in file_filters].index(used_filter)
		used_filter = file_filters[used_filter]
		assert isinstance(used_filter, fs.FileFilter)

	if mode != file_mode.FILES_MULTIPLE:
		choice = choice[0]

	if return_filter:
		return choice, return_filter
	return choice