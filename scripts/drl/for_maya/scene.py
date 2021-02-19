__author__ = 'Lex Darlog (DRL)'

from maya import cmds

from drl.for_maya import ui, info
from drl_common import errors as err
from drl_py23 import (
	str_t as _str_t,
	str_h as _str_h,
)
import sys as __sys
__self_module = __sys.modules[__name__]


class DefaultSaveChangesDialog(object):
	"""
	Python class for displaying save dialog when scene is changed.

	:param message: <None/str> Override default text/question in the dialog window.
	:param title: <None/str> Override default window title.
	:param save: <None/str> Name of the "Save" button.
	:param don_t: <None/str> Name of the "Don't save" button.
	:param cancel: <None/str> Name of the "Cancel" button.
	:param display_don_t: <bool> Whether the middle "Don't save" button is displayed.
	:param icon: <None/str> Optional big icon displayed on the left from the message text. Use ui.dialogs.confirm_icon as enum for available values.
	"""

	b_save = ui.Resource('s_TdialogStrings.rSave')
	b_don_t_save = ui.Resource('s_TdialogStrings.rDontSave')
	b_cancel = ui.Resource('s_TdialogStrings.rCancel')

	message_template = ui.Resource('m_saveChanges.kSaveFileMsg')
	message_untitled = ui.Resource('m_saveChanges.kSaveChangesToUntitled')
	message_ple = ui.Resource('m_saveChanges.kMayaPersonalLearning')
	title_normal = ui.Resource('m_saveChanges.kSaveChanges')
	title_untitled = ui.Resource('m_saveChanges.kWarningSceneNotSaved')

	is_ple = info.is_ple()
	maya_ext = ('.ma', '.mb')
	ple_ext = '.mp'

	def __init__(
		self,
		message=None, title=None,
		save=None, don_t=None, cancel=None,
		display_don_t=True, icon=None
	):
		super(DefaultSaveChangesDialog, self).__init__()
		self.message = message
		self.title = title
		self.file = name()
		self.save = save
		self.don_t = don_t
		self.cancel = cancel
		self.display_don_t = display_don_t
		self.icon = icon

	def get_fields_values(self):
		"""
		Generate the actual string values for dialog window.

		:return: <tuple> of <strings>:

			* message
			* title
			* button "Save" (Yes)
			* button "Don't save"
			* button "Cancel" (No/Esc)
		"""
		self.file = nm = name()
		c = self.__class__

		def default_message(file_name):
			if not file_name:
				return c.message_untitled.value()

			if not c.is_ple:
				return c.message_template.value_formatted(file_name)

			from os import path
			folder, base_old_nm = path.split(file_name)
			assert isinstance(folder, _str_t)
			assert isinstance(base_old_nm, _str_t)
			slash = file_name[:]
			if folder:
				slash = slash[len(folder):]
			if base_old_nm:
				slash = slash[:-len(base_old_nm)]
			base_no_ext, ext = path.splitext(base_old_nm)
			assert isinstance(base_old_nm, _str_t)
			assert isinstance(ext, _str_t)
			if ext.lower() in c.maya_ext:
				ext = c.ple_ext
			file_name = folder + slash + base_no_ext + ext
			return c.message_ple.value_formatted(base_old_nm, file_name)

		def value(arg, arg_nm, default):
			return err.NotStringError(arg, arg_nm).raise_if_needed() if arg else default.value()

		msg = self.message
		msg = err.NotStringError(msg, 'message').raise_if_needed() if msg else default_message(nm)

		title = value(self.title, 'title', c.title_normal if nm else c.title_untitled)
		save = value(self.save, 'save', c.b_save)
		don_t = value(self.don_t, 'don_t', c.b_don_t_save)
		cancel = value(self.cancel, 'cancel', c.b_cancel)

		return msg, title, save, don_t, cancel

	def show_prompt_if_changed(self):
		"""
		If scene has unsaved changes, show the dialog window asking to save it.

		:return: tuple of 2 items:

			* <bool> whether scene is modified
			* <int> what user has selected:
				* 0 - Esc / Cancel
				* 1 - Save (default button)
				* 2 - Don't save
		"""
		changed = unsaved_changes()
		message, title, save, don_t, cancel = self.get_fields_values()
		choice = 0
		if changed:
			choice = ui.dialogs.confirm(
				title, message,
				yes=save, no=cancel,
				extra_buttons=(don_t if self.display_don_t else None),
				icon=self.icon
			)
		return changed, choice

	def save_if_changed(self):
		"""
		If the scene is modified, show the dialog.

		If user selected to save the scene, do it with the default Maya behavior.

		:return: tuple of 2 items:

			* <bool> whether scene was modified (so the dialog had pop up)
			* <int> what user has selected:
				* 0 - Esc / Cancel
				* 1 - Save (default button)
				* 2 - Don't save
				* -1 - User selected 'Save' in the main dialog in untitled scene.
					But after the dialog window 'Save As' has pop up, they have closed it.
		"""
		changed, choice = self.show_prompt_if_changed()
		if changed and choice == 1:
			if self.file:
				save()
			else:
				save_as()
				self.file = nm = name()
				if not nm:
					choice = -1
		return changed, choice


def name():
	"""
	The name of currently opened scene.

	:return: <str> Scene path. Empty string if untitled scene.
	"""
	n = cmds.file(q=1, sceneName=1)
	assert isinstance(n, _str_t)
	return n


def save():
	"""
	Perform save the same way Maya does it.

	:return: whatever Maya's save returns.

		* It should be the saved file's path.
		* But could be None if error occurs during save.
	"""
	return cmds.SaveScene()


def save_as():
	"""
	Perform "Save As" operation the same way Maya does it.

	:return: whatever Maya's <SaveSceneAs> returns.

		* It should be the saved file's path.
		* But could be None if error occurs during save.
	"""
	return cmds.SaveSceneAs()


def unsaved_changes():
	u = cmds.file(q=True, modified=True)
	if not isinstance(u, bool):
		u = bool(u)
	assert isinstance(u, bool)
	return u