from drl_common import filesystem as fs

__author__ = 'DRL'

import os

from pymel import core as pm

from drl_common.strings import str_t
from drl.for_maya import ls
from . import info as inf


class Preset(object):
	def __init__(self, name, is_export=True):
		"""
		The class providing different data for FBX presets.

		:param name: (string) the name of the FBX preset (or Preset object)
		:param is_export: (bool) whether the given preset is export preset (import otherwise)
		"""
		super(Preset, self).__init__()

		if isinstance(name, Preset):
			is_export = name.is_export
			name = name.name

		self._name = ''
		self.__set_name(name)
		self._is_export = True
		self.__set_type(is_export)

	def __set_name(self, name):
		if not isinstance(name, str_t):
			raise Exception('Wrong type for <name>. String expected, got: ' + repr(name))
		if name == '':
			raise Exception('Empty string provided as preset name.')
		self._name = name

	def __set_type(self, is_export=True):
		if not isinstance(is_export, bool):
			is_export = bool(is_export)
		self._is_export = is_export

	@property
	def name(self):
		return self._name

	@name.setter
	def name(self, value):
		self.__set_name(value)

	@property
	def is_export(self):
		return self._is_export

	@is_export.setter
	def is_export(self, value):
		self.__set_type(value)

	@staticmethod
	def presets_path():
		"""
		Returns path to the Maya's FBX presets folder.
		"""
		app_dir = inf.get_maya_app_dir()
		fbx_dir = os.path.join(app_dir, 'FBX/Presets')
		fbx_dir = fbx_dir.replace('\\', '/')
		return fbx_dir

	@staticmethod
	def is_preset_extention(ext='', is_export=True):
		"""
		Checks whether the given file extention is FBX preset

		:param ext: file extention, including dot character
		:param is_export: if True, the check performed for export preset, otherwise for import preset
		:return: True if the given extention is FBX preset of the given type, False otherwise
		"""
		return (
			(ext == '.fbxexportpreset' and is_export) or
			(ext == '.fbximportpreset' and not is_export)
		)

	def path(self):
		"""
		Finds the actual filepath of the preset with the given name.
		If there are several copies of the same preset for different FBX versions, the last one is used.

		:return: absolute path to the file containing this preset
		"""
		fbx_dir = self.presets_path()
		preset = ''
		for root, dirs, files in os.walk(fbx_dir):
			for f in files:
				f_ext = os.path.splitext(f)
				if f_ext[0] == self.name and self.is_preset_extention(f_ext[1], self.is_export):
					preset = os.path.join(root, f)
					preset = preset.replace('\\', '/')
		return preset

	def load(self):
		load_func = pm.mel.FBXLoadExportPresetFile if self.is_export else pm.mel.FBXLoadImportPresetFile
		load_func(f=self.path())


class Export(object):
	def __init__(self, path, objects=None, selection_if_none=True):
		"""
		The class providing export functionality.

		:param path: (str) path for the exported file (or root folder, for multi-export)
		:param objects: (str/list) objects to export
		:param selection_if_none: (bool) whether to use selection if <objs> is None
		:return:
		"""
		super(Export, self).__init__()
		self._path = ''
		self.__set_path(path)
		self._objects = []
		self.__set_objects(objects, selection_if_none)

	def __set_objects(self, objects=None, selection_if_none=True):
		objects = ls.pymel.default_input.handle_input(objects, selection_if_none)
		if not objects:
			raise Exception('No objects provided for export!')
		self._objects = objects

	def __set_path(self, path):
		if not isinstance(path, str_t):
			raise Exception('Wrong type for <path> property. String expected, got: ' + repr(path))
		if not path:
			raise Exception('Empty string is given as <path> property.')
		self._path = path.replace('\\', '/')

	@property
	def objects(self):
		return self._objects

	@objects.setter
	def objects(self, value):
		self.__set_objects(value, False)

	def objects_from_selection(self):
		self.__set_objects()

	@property
	def path(self):
		return self._path

	@path.setter
	def path(self, value):
		self.__set_path(value)

	def path_to_file(self):
		"""
		Returns the path to an FBX file, ensuring it has proper extension.
		"""
		fbx_path = self.path
		ext = os.path.splitext(fbx_path)[1]
		if not ext or ext.lower() != '.fbx':
			fbx_path += '.fbx'
		return fbx_path

	@staticmethod
	def _apply_preset_if_not_none(preset=None):
		if not preset is None:
			Preset(preset, is_export=True).load()

	def to_file(self, preset=None):
		"""
		Exports given objects to the FBX file.

		:param preset: (str/Preset) optional argument, defining FBX export preset
		:return: full path to the exported file
		"""
		fbx_path = self.path_to_file()
		objs = self.objects

		prev_sel = pm.ls(sl=True)

		self._apply_preset_if_not_none(preset)

		pm.select(objs, r=True)
		fs.clean_path_for_file(fbx_path, overwrite_folders=1, remove_file=1)
		pm.mel.FBXExport(f=fbx_path, s=True)

		if prev_sel:
			pm.select(prev_sel, r=True)
		else:
			pm.select(cl=True)

		return fbx_path

	def to_multiple_files(self, preset=None):
		"""
		Exports each of given objects to a separate FBX file.

		:param preset: (str/Preset) optional argument, defining FBX export preset
		:return: (list of str) full paths to the exported files
		"""
		dir_path = self.path
		objects = self.objects[:]
		self._apply_preset_if_not_none(preset)
		res = []

		for o in objects:
			name = ls.pymel.short_item_name(o)
			self.objects = o
			self.path = os.path.join(dir_path, name)
			res.append(self.to_file(preset=None))

		self.objects = objects
		self.path = dir_path

		return res