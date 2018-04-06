__author__ = 'DRL'

import os

from pymel import core as pm

from drl.for_maya import info as inf
from drl.for_maya import plugins
from drl.for_maya.ls import pymel as ls
from drl.for_maya.ui import dialogs

from drl_common import utils
from drl_common import errors as err
from drl_common import filesystem as fs

from . import errors
from . import messages as m

from drl.for_maya import py_node_types as _pnt
_t_transform = _pnt.transform
_t_shape_any = _pnt.shape.any
_t_comp_any = _pnt.comp.any
_tt_geo_any = (_pnt.transform, _pnt.shape.any, _pnt.comp.any)


_is_str = lambda x: isinstance(x, (str, unicode))


class FBX(plugins.Plugin):
	"""
	Base class for handling FBX plugin. Normally, you don't need to use it directly,
	but instead you call either of it's child classes: Import or Export.
	"""
	def __init__(self, auto_load_if_needed=True, settings_version=None, plugin='fbxmaya'):
		super(FBX, self).__init__(plugin)

		self.__load = bool(auto_load_if_needed)
		self._set_version(settings_version)


	def _set_version(self, settings_version):
		if settings_version is None:
			settings_version = super(FBX, self).version(self.__load)
		else:
			err.NotStringError(settings_version, 'settings_version').raise_if_needed()
		self.__version = settings_version


	@property
	def settings_version(self):
		"""
		The version of FBX used for settings. By default, it's the current plugin's version.

		:rtype: str|unicode
		"""
		return self.__version

	@settings_version.setter
	def settings_version(self, value):
		self._set_version(value)


	@property
	def auto_load_if_needed(self):
		"""
		Whether this class will try to load plugin automatically if needed.

		If False, the error is thrown when the module try to access the plugin's data.
		:rtype: bool
		"""
		return self.__load

	@auto_load_if_needed.setter
	def auto_load_if_needed(self, value):
		self.__load = bool(value)


	def presets_path(self):
		"""
		Returns path to the default Maya's FBX presets folder
		for the current FBX plugin version.

		:return: absolute folder path, with unix-style slashes. No trailing slash.
		:rtype: str|unicode
		"""
		app_dir = inf.get_maya_app_dir()

		fbx_dir = os.path.join(app_dir, 'FBX/Presets', self.__version)
		return fbx_dir.replace('\\', '/').rstrip('/')


# -----------------------------------------------------------------------------


class _ImportExportBase(FBX):
	"""
	The base class containing common methods for both import and export process.
	"""
	def __init__(
		self,
		auto_load_if_needed=True, settings_version=None, plugin='fbxmaya',
		path_postfix='import', ext='.fbximportpreset'
	):
		super(_ImportExportBase, self).__init__(auto_load_if_needed, settings_version, plugin)
		self.__path_postfix = path_postfix
		self.__ext = ext
		self.__ext_len = len(ext)

	def presets_path(self):
		"""
		Returns path to the folder containing presets.

		:return: absolute folder path, with unix-style slashes. No trailing slash.
		:rtype: str|unicode
		"""
		return '/'.join([super(_ImportExportBase, self).presets_path(), self.__path_postfix])

	@staticmethod
	def _check_preset_name(preset):
		"""
		Ensures the preset name is non-empty string.

		:raises: <WrongPresetNameError> if check is failed.
		"""
		if not (_is_str(preset) and preset):
			raise errors.WrongPresetNameError(preset)

	def preset_path(self, preset):
		"""
		High-level cleanup of a given <preset> argument.

		It ensures the given <preset> is a string and, if necessary, converts the short name to a full path.

		:type preset: str|unicode
		:return: full path to the preset file
		:rtype: str|unicode
		"""
		_ImportExportBase._check_preset_name(preset)
		preset = preset.replace('\\', '/').rstrip('/')
		if len(preset.split('/')) < 2:
			preset = '/'.join([self.presets_path(), preset])
		ext = self.__ext
		if not preset.lower().endswith(ext.lower()):
			preset += ext
		return preset

	@staticmethod
	def _preset_exists(preset_path):
		"""
		Whether preset file exists at the given path.

		No name-to-path conversion performed, it's your responsibility to make sure
		you're providing a full path.

		:type preset_path: str|unicode
		:rtype: bool
		"""
		_ImportExportBase._check_preset_name(preset_path)
		preset_path = preset_path.replace('\\', '/').rstrip('/')
		return os.path.exists(preset_path) and os.path.isfile(preset_path)

	@staticmethod
	def _check_preset_exists(preset_path):
		"""
		Ensures preset file exists at the given path.

		:raises: <PresetDoesntExistError> if such file is not found.
		"""
		if not _ImportExportBase._preset_exists(preset_path):
			raise errors.PresetDoesntExistError(preset_path)

	def preset_exists(self, preset):
		"""
		Whether given preset file exists.

		:type preset: str|unicode
		:rtype: bool
		"""
		return _ImportExportBase._preset_exists(self.preset_path(preset))

	def _load_preset(self, preset, load_f):
		"""
		Wrapper method. Loads the given preset with the given function.

		:param preset:
			Preset name/path.
			If name is given, the full path is generated automatically.
		:type preset: str|unicode
		:param load_f:
			Function which takes exactly one argument (path)
			and performs the preset loading.
		"""
		preset_path = self.preset_path(preset)
		_ImportExportBase._check_preset_exists(preset_path)
		load_f(preset_path)


# -----------------------------------------------------------------------------


class Importer(_ImportExportBase):
	"""
	The class handling FBX import process.
	"""
	def __init__(
		self,
		auto_load_if_needed=True, settings_version=None, plugin='fbxmaya'
	):
		super(Importer, self).__init__(
			auto_load_if_needed, settings_version, plugin,
			'import', '.fbximportpreset'
		)

	def load_preset(self, preset):
		"""
		Loads given FBX-import preset.

		:param preset:
			Preset name/path.
			If a short name is given, it's turned into the full path automatically.
		:type preset: str|unicode
		:return: self
		"""
		self._load_preset(preset, lambda fl: pm.mel.FBXLoadImportPresetFile(f=fl))
		return self

	@staticmethod
	def do_import(fbx_file, take_index=-1):
		"""
		Performs the actual import.

		The import settings need to be already specified.
		You can use `load_preset()` for that.

		:param fbx_file: path to the imported file.
		:type fbx_file: str|unicode
		:param take_index:
			the number of Take, imported from the file:
				* 0 = No Animation
				* -1 = the last take in the array.
				* 1..N = Take at the given number, where N is the total number of takes
				* if less then -1 or more then N, an error is thrown.
		:type take_index: int
		"""
		err.NotStringError(fbx_file, 'fbx_file').raise_if_needed()
		fbx_file = fbx_file.replace('\\', '/').rstrip('/')
		pm.mel.FBXImport(f=fbx_file, t=take_index)


# -----------------------------------------------------------------------------


class Exporter(_ImportExportBase):
	"""
	The class handling FBX export process.

	Most methods return the called instance of this class itself (i.e. <self>),
	which allows you to just perform actions in chain.
	"""
	def __init__(
		self,
		auto_load_if_needed=True, settings_version=None, plugin='fbxmaya'
	):
		super(Exporter, self).__init__(
			auto_load_if_needed, settings_version, plugin,
			'export', '.fbxexportpreset'
		)
		self.__objects = list()

	@staticmethod
	def _filter_objects(objects):
		"""
		Turns the given objects to a unified form. I.e., converts the objects you provide
		to a flat list, containing only PyMel's transforms and shapes.

		Selected components are converted to their corresponding shapes.

		:type objects:
			str|unicode|pm.PyNode|list[str|unicode|pm.PyNode]|tuple[str|unicode|pm.PyNode]
		"""
		return [
			(o.node() if isinstance(o, _t_comp_any) else o) for o in
			ls.default_input.handle_input(objects, False)
			if isinstance(o, _tt_geo_any)
		]

	def set_objects(self, objects):
		"""
		:type objects:
			str|unicode|pm.PyNode|list[str|unicode|pm.PyNode]|tuple[str|unicode|pm.PyNode]
		"""
		self.__objects = Exporter._filter_objects(objects)
		return self

	def add_objects(self, objects):
		"""
		Add the given objects to the list of what's going to be exported.

		Only transforms and shapes are included.
		Given components are converted to their corresponding shapes.

		:type objects:
			str|unicode|pm.PyNode|list[str|unicode|pm.PyNode]|tuple[str|unicode|pm.PyNode]
		"""
		self.__objects += Exporter._filter_objects(objects)
		return self

	def add_selected_objects(self):
		"""
		Add selected objects to the list of what's going to be exported.

		Only transforms and shapes are included.
		Given components are converted to their corresponding shapes.
		"""
		self.__objects += Exporter._filter_objects(pm.ls(sl=1))
		return self

	def get_objects_raw(self):
		"""
		Returns the exact list of objects marked for export.

		All their hierarchy, grandchildren etc. will be exported.

		:rtype: list[pm.PyNode]
		"""
		return self.__objects[:]

	def get_objects_with_children(self, keep_order=False):
		"""
		Get the list of actual objects that will be exported.

		I.e., all off the children, grand-children of the objects
		that were actually marked for export are also returned.

		:param keep_order:
			Leave it to false if the order doesn't matter. It will work faster.
		:return:
			list of transforms/shapes of the exported objects
			+ all their child transforms.
		"""
		if keep_order:
			return ls.to_hierarchy(
				self.__objects, False,
				remove_duplicates=True
			)
		return list(
			set(ls.to_hierarchy(self.__objects, False))
		)

	def load_preset(self, preset):
		"""
		Loads given FBX-export preset.

		:param preset:
			Preset name/path.
			If name is given, the full path is generated automatically.
		:type preset: str|unicode
		"""
		self._load_preset(preset, lambda fl: pm.mel.FBXLoadExportPresetFile(f=fl))
		return self

	@staticmethod
	def cleanup_fbx_file_path(fbx_file, overwrite=2):
		"""
		Error-check for the given file path during export.

		:param fbx_file: path to the file.
		:type fbx_file: str|unicode
		:param overwrite:
			whether existing file is overwritten:
				* 0 - don't overwrite (an error is thrown if file already exist)
				* 1 - overwrite
				* 2 - confirmation dialog will pop up if file already exist
		:return:
			3 results:
				*
					Cleaned-up path on success.
					I.e., unix-style slashes, removed extra trailing/leading slashes.
				* Whether the path was cleaned-up (removed folder/file at this path)
				*
					Whether interactive dialog was shown to a user
					**AND** they have chosen to cancel overwrite process
					(i.e., path was **not** cleaned).
		"""
		err.NotStringError(fbx_file, 'fbx_file').raise_if_needed_or_empty()
		fbx_file = fs.to_unix_path(fbx_file, trailing_slash=False)
		while '//' in fbx_file:
			fbx_file = fbx_file.replace('//', '/')
		if not fbx_file.lower().endswith('.fbx'):
			fbx_file += '.fbx'
		return fs.clean_path_for_file(fbx_file, 2, overwrite)

	@staticmethod
	def export_scene(fbx_file, overwrite=2):
		"""
		Export the entire Maya scene to the given FBX file.

		The export settings need to be already specified. You can use load_preset() for that.

		:param fbx_file: path to the file.
		:type fbx_file: str|unicode
		:param overwrite:
			whether existing file is overwritten:
				* 0 - don't overwrite (an error is thrown if file already exist)
				* 1 - overwrite
				* 2 - confirmation dialog will pop up if file already exist
		:return:
			3 results:
				* the exported file path (the string could be cleaned up).
				* Whether the path was overwritten by a new FBX
				*
					Whether interactive dialog was shown to a user
					**AND** they have chosen **NOT** to overwrite existing file/folder.
		"""
		fbx_file, removed, cancelled = Exporter.cleanup_fbx_file_path(
			fbx_file, overwrite
		)
		if not cancelled:
			sel = pm.ls(sl=1)
			pm.select(cl=1)
			pm.mel.FBXExport(f=fbx_file)
			pm.select(sel, r=1, ne=1)
		return fbx_file, removed, cancelled

	def export_objects(self, fbx_file, overwrite=2):
		"""
		Export the specified objects to the given FBX file.

		You can specify objects with add_objects() or set_objects() method.

		The export settings need to be already specified. You can use load_preset() for that.

		:param fbx_file: path to the file.
		:type fbx_file: str|unicode
		:param overwrite:
			whether existing file is overwritten:
				* 0 - don't overwrite (an error is thrown if file already exist)
				* 1 - overwrite
				* 2 - confirmation dialog will pop up if file already exist
		:return:
			3 results:
				* the exported file path (the string could be cleaned up).
				* Whether the path was overwritten by a new FBX
				*
					Whether interactive dialog was shown to a user
					**AND** they have chosen **NOT** to overwrite existing file/folder.
		"""
		if not self.__objects:
			raise errors.NothingToExportError(self.__id)

		objects = self.get_objects_with_children()
		if not objects:
			raise errors.NothingToExportError(self.__id)
		fbx_file, removed, cancelled = Exporter.cleanup_fbx_file_path(
			fbx_file, overwrite
		)
		if not cancelled:
			sel = pm.ls(sl=1)
			pm.select(objects, r=1, ne=1)
			pm.mel.FBXExport(f=fbx_file, s=1)
			pm.select(sel, r=1, ne=1)
		return fbx_file, removed, cancelled



class BatchExporter(object):
	def __init__(
		self, folder='',
		auto_load_if_needed=True, settings_version=None, plugin='fbxmaya'
	):
		super(BatchExporter, self).__init__()
		self._exporter = Exporter(auto_load_if_needed, settings_version, plugin)
		self.__folder = ''
		self.__set_folder(folder)
		self.__parent_groups = list()

	def __set_folder(self, path):
		if not path:
			self.__folder = ''
			return

		err.NotStringError(path, 'folder').raise_if_needed()
		self.__folder = path

	def set_folder(self, path):
		self.__set_folder(path)
		return self

	@property
	def folder(self):
		return self.__folder

	@folder.setter
	def folder(self, value):
		self.__set_folder(value)

	def load_preset(self, preset):
		self._exporter.load_preset(preset)
		return self

	@staticmethod
	def _filter_objects(objects):
		res = list()
		append = res.append
		nt = pm.nt
		objects = ls.default_input.handle_input(objects, False)
		for o in objects:
			if isinstance(o, _t_comp_any):
				append(o.node().parent(0))
			elif isinstance(o, _t_shape_any):
				append(o.parent(0))
			elif isinstance(o, _t_transform):
				append(o)
			else:
				raise err.WrongTypeError(o, _tt_geo_any, 'group')
		return res

	def set_groups(self, objects):
		"""
		Set object groups.

		Each group will be exported as a separate fbx file, with the same name.
		"""
		self.__parent_groups = BatchExporter._filter_objects(objects)
		return self

	def add_groups(self, objects):
		"""
		Add object groups.
		If this group already exists in the list, it's not added (automatic duplicates prevention).

		Each group will be exported as a separate fbx file, with the same name.
		"""
		if not objects:
			return self
		objects = BatchExporter._filter_objects(objects)
		if not objects:
			return self
		self.__parent_groups = utils.remove_duplicates(
			self.__parent_groups + objects
		)
		return self

	def add_selected_groups(self):
		"""
		Add selected objects as export groups.
		If this group already exists in the list, it's not added (automatic duplicates prevention).

		Each group will be exported as a separate fbx file, with the same name.
		"""
		sel = pm.ls(sl=1)
		if not sel:
			return self
		sel = BatchExporter._filter_objects(sel)
		if not sel:
			return self
		self.__parent_groups = utils.remove_duplicates(
			self.__parent_groups + sel
		)
		return self

	def get_groups(self):
		return self.__parent_groups[:]

	def get_group_objects(self, x, keep_order=False):
		exp = self._exporter
		gr = self.__parent_groups[x]
		exp.set_objects(gr)
		return exp.get_objects_with_children(keep_order)

	def get_exporter(self):
		return self._exporter


	def __export_as_group(self, gr, overwrite=2):
		"""
		Performs the actual export of a group.

		:param gr: PyNode transform, the group object.
		:type gr: pm.PyNode|pm.nodetypes.Transform
		:param overwrite:
			whether existing file is overwritten:
				* 0 - don't overwrite (an error is thrown if file already exist)
				* 1 - overwrite
				* 2 - confirmation dialog will pop up if file already exist
		:return:
			3 results:
				* the exported file path (the string could be cleaned up).
				* Whether the path was overwritten by a new FBX
				*
					Whether interactive dialog was shown to a user
					**AND** they have chosen **NOT** to overwrite existing file/folder.
		"""
		nm = ls.short_item_name(gr)
		path = self.__folder
		if not path:
			raise fs.errors.EmptyPathError(path, 'FBX root folder is not specified')
		path = fs.clean_path_for_folder(path, 2).rstrip('/')
		self.__folder = path
		path += '/%s.fbx' % nm
		return self._exporter.set_objects(gr).export_objects(path, overwrite)

	def _get_folder_dialog(self, start_path=None, raise_error_if_cancelled=True):
		"""
		Let user specify the export folder by opening the dialog.

		The confirmation will pop up if user cancels the dialog.

		:return:
			* <str> selected folder path
			* <None> if raise_error_if_cancelled == False, and user has cancelled the dialog box.
		:raises ExportAbortedError: if raise_error_if_cancelled and user has cancelled the dialog box.
		"""
		folder = None
		if not start_path:
			start_path = self.__folder

		while True:
			folder = dialogs.file_chooser(
				m.DIR_TITLE, dialogs.file_mode.DIR_DISPLAY_FILES,
				m.DIR_YES, m.DIR_NO,
				starting_directory=(start_path if start_path else None)
			)
			if folder:
				assert _is_str(folder)
				folder = folder.replace('\\', '/')
				if folder != '/':
					folder = folder.rstrip('/')
				break

			cancel_export = dialogs.confirm(
				m.CANCEL_TITLE, m.CANCEL_MESSAGE,
				yes=(m.CANCEL_YES, m.CANCEL_YES_TIP),
				no=(m.CANCEL_NO, m.CANCEL_NO_TIP),
				icon=dialogs.confirm_icon.QUESTION
			)
			if cancel_export:
				break

		if not folder and raise_error_if_cancelled:
			raise errors.ExportAbortedError(self._exporter.id)
		return folder

	def export_group(self, x, overwrite=2):
		"""
		Export the group at the given index (start from 0).

		:param x: <int> the index of a group (in the groups list).
		:param overwrite: <int>, whether existing file is overwritten:

			* 0 - don't overwrite (an error is thrown if file already exist)
			* 1 - overwrite
			* 2 - confirmation dialog will pop up if file already exist
		:return:
			3 results:
				* the exported file path (the string could be cleaned up).
				* Whether the path was overwritten by a new FBX
				*
					Whether interactive dialog was shown to a user
					**AND** they have chosen **NOT** to overwrite existing file/folder.
		"""
		err.WrongTypeError(x, int, 'index').raise_if_needed()
		groups = self.__parent_groups
		if not groups:
			raise errors.NothingToExportError(self._exporter.name)
		return self.__export_as_group(groups[x], overwrite)

	def export_group_dialog(self, x, overwrite=2):
		"""
		Export the group at the given index (start from 0).
		The path is specified in process by opening file chooser dialog window.

		:param x: the index of a group (in the groups list).
		:type x: int
		:param overwrite:
			Whether existing file is overwritten:
				* 0 - don't overwrite (an error is thrown if file already exist)
				* 1 - overwrite
				* 2 - confirmation dialog will pop up if file already exist
		:return:
			3 results:
				* the exported file path (the string could be cleaned up).
				* Whether the path was overwritten by a new FBX
				*
					Whether interactive dialog was shown to a user
					**AND** they have chosen **NOT** to overwrite existing file/folder.
		"""
		err.WrongTypeError(x, int, 'index').raise_if_needed()
		groups = self.__parent_groups
		if not groups:
			raise errors.NothingToExportError(self._exporter.name)
		gr = groups[x]  # force an IndexError to be thrown if out of range

		folder_path = self._get_folder_dialog()
		return self.set_folder(folder_path).__export_as_group(gr, overwrite)

	def export_all_groups(self, overwrite=2):
		"""
		Export all the groups.

		:param overwrite:
			whether existing file is overwritten:
				* 0 - don't overwrite (an error is thrown if file already exist)
				* 1 - overwrite
				* 2 - confirmation dialog will pop up if file already exist
		:return: the paths of the exported files (each string could be cleaned up).
		"""
		groups = self.__parent_groups
		if not groups:
			raise errors.NothingToExportError(self._exporter.name)
		return [
			path for path, replaced, cancelled in
			(self.__export_as_group(gr, overwrite) for gr in groups)
			if not cancelled
		]

	def export_all_groups_dialog(self, overwrite=2):
		"""
		Export all the groups.
		The path is specified in process by opening file chooser dialog window.

		:param overwrite:
			Whether existing file is overwritten:
				* 0 - don't overwrite (an error is thrown if file already exist)
				* 1 - overwrite
				* 2 - confirmation dialog will pop up if file already exist
		:return: The paths of the exported files (each string could be cleaned up).
		"""
		groups = self.__parent_groups
		if not groups:
			raise errors.NothingToExportError(self._exporter.name)

		folder_path = self._get_folder_dialog()
		self.set_folder(folder_path)
		return [
			path for path, replaced, cancelled in
			(self.__export_as_group(gr, overwrite) for gr in groups)
			if not cancelled
		]
