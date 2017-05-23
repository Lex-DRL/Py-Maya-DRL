__author__ = 'DRL'

from drl.for_maya import plugins


class BaseError(plugins.PluginBaseError):
	"""
	Base FBX exceptions class.
	"""
	def __init__(self, error_details='<undefined>', plugin='fbxmaya'):
		super(BaseError, self).__init__(plugin)
		self._msg_formatter = 'FBX error: %s'
		self.message = self._msg_formatter % error_details
		self.error_details = error_details

	def _construct_message(self):
		return self._msg_formatter % self.error_details


class ImportError(BaseError):
	"""
	Errors caused by <Import> class.
	"""
	def __init__(self, error_details='<undefined>', plugin='fbxmaya'):
		super(ImportError, self).__init__(error_details, plugin)
		self._msg_formatter = 'FBX import error: %s'
		self._update_message()


class ExportError(BaseError):
	"""
	Errors caused by <Export> class.
	"""
	def __init__(self, error_details='<undefined>', plugin='fbxmaya'):
		super(ExportError, self).__init__(error_details, plugin)
		self._msg_formatter = 'FBX export error: %s'
		self._update_message()


class NothingToExportError(ExportError):
	"""
	We're trying to export nothing.
	"""
	def __init__(self, plugin='fbxmaya'):
		super(NothingToExportError, self).__init__('Nothing to export', plugin)


class ExportAbortedError(ExportError):
	"""
	The export process fas been interrupted by a user.
	"""
	def __init__(self, plugin='fbxmaya'):
		super(ExportAbortedError, self).__init__('Export aborted', plugin)




# -----------------------------------------------------------------------------


class PresetBaseError(Exception):
	def __init__(self, preset, formatted_message='Preset error: {0!r}', **message_data):
		message = formatted_message.format(preset, **message_data)
		super(PresetBaseError, self).__init__(message)
		self.preset = preset
		self.data = message_data


class WrongPresetNameError(PresetBaseError):
	"""
	The provided preset name isn't valid.

	It's either an empty string or not string at all.
	"""
	def __init__(self, preset):
		super(WrongPresetNameError, self).__init__(preset, 'Wrong preset name: {0!r}')


class PresetDoesntExistError(PresetBaseError):
	"""
	The given preset name is valid string, but this preset doesn't exist.
	"""
	def __init__(self, preset):
		super(PresetDoesntExistError, self).__init__(preset, "Preset doesn't exist: {0!r}")
