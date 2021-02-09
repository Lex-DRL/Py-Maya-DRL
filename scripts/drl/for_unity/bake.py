__author__ = 'DRL'

from drl_common.strings import *
from drl_common.py_2_3 import (
	str_t as _str_t,
	str_h as _str_h,
	t_strict_str as _str,
	t_strict_unicode as _unicode,
)
from drl.for_maya import ls
from pymel import core as pm
import os, sys
import warnings as wrn
import datetime as dt

time_error_treshold = 2.0
sleep_time = 3.0


class BatchRender(object):
	def __init__(self, start_frame=None, end_frame=None):
		super(BatchRender, self).__init__()
		self.__start = 0
		self.__end = 0
		self.__set_start(start_frame)
		self.__set_end(end_frame)

	def __set_start(self, value):
		if value is None:
			value = int(pm.playbackOptions(q=True, minTime=True))
		if not isinstance(value, int):
			value = int(value)
		assert isinstance(value, int)
		self.__start = value
		if self.__end < value:
			self.__end = value

	def __set_end(self, value):
		if value is None:
			value = int(pm.playbackOptions(q=True, maxTime=True))
		if not isinstance(value, int):
			value = int(value)
		assert isinstance(value, int)
		self.__end = value
		if self.__start > value:
			self.__start = value

	@property
	def start_frame(self):
		return self.__start
	@start_frame.setter
	def start_frame(self, value):
		self.__set_start(value)

	@property
	def end_frame(self):
		return self.__end
	@end_frame.setter
	def end_frame(self, value):
		self.__set_end(value)

	def render_range(self):
		for i in xrange(self.start_frame, self.end_frame + 1):
			pm.currentTime(i)
			print('Rendering frame: ' + str(i))
			pm.runtime.RedoPreviousRender()

	@staticmethod
	def render_current_frame():
		pm.runtime.RedoPreviousRender()



class Turtle(object):
	__layerNodeType = 'ilrBakeLayer'
	__defaultNodeName = 'TurtleDefaultBakeLayer'
	__textureDirAttrib = 'tbDirectory'
	__textureFileAttrib = 'tbFileName'
	__resAttrib_x = 'tbResX'
	__resAttrib_y = 'tbResY'
	__drl_tmp_extra_path = 'drl_tmp_turtle'
	__turtleOptionsNode = 'TurtleRenderOptions'
	__turtleBakeModeAttr = 'renderer'

	# auto-generated constants:
	__drl_tmp_postfix = os.path.join(__drl_tmp_extra_path, '').replace('\\', '/')
	__drl_tmp_postfix_len = len(__drl_tmp_postfix)

	def __init__(self, bake_layer_node=None, to_exr=False):
		super(Turtle, self).__init__()
		self.__initialisation = True
		self.__set_layer_node(bake_layer_node)
		self.__initialisation = None
		self.__to_exr = to_exr

	def __set_layer_node(self, bake_layer_node=None):
		node = bake_layer_node
		if isinstance(node, set):
			node = list(node)
		if isinstance(node, (list, tuple)):
			if not node:
				if not self.__initialisation:
					raise Exception("Empty list is given. Turtle's layer node expected.")
				node = ''
			else:
				if len(node) > 1:
					raise Exception('Single Turtle node expected. Multiple provided: ' + repr(node))
				node = node[0]

		if self.__initialisation:
			if not node:
				node = ''
			if not pm.objExists(node):
				node = Turtle.__defaultNodeName
		if not pm.objExists(node):
			raise Exception("Given node doesn't exist: " + node)
		if isinstance(node, _str_t):
			node = pm.PyNode(node)

		assert isinstance(node, pm.PyNode)
		if node.nodeType() != Turtle.__layerNodeType:
			raise Exception("Given node isn't a Turtle's Bake Layer: " + node)
		self.__layerNode = node

	@staticmethod
	def get_instance(turtle_node=None):
		if (
			turtle_node is None or
			isinstance(turtle_node, (pm.PyNode, _str, _unicode, list, tuple, set))
		):
			turtle_node = Turtle(turtle_node)
		assert isinstance(turtle_node, Turtle)
		return turtle_node

	@property
	def layer_node(self):
		return self.__layerNode
	@layer_node.setter
	def layer_node(self, value):
		self.__set_layer_node(value)

	def __attr(self, attrib_name=''):
		a = self.layer_node.attr(attrib_name)
		assert isinstance(a, pm.Attribute)
		return a

	@property
	def dir_attrib(self):
		return self.__attr(Turtle.__textureDirAttrib)

	@property
	def filename_attrib(self):
		return self.__attr(Turtle.__textureFileAttrib)

	@property
	def resolution_attrib_x(self):
		return self.__attr(Turtle.__resAttrib_x)
	@property
	def resolution_attrib_y(self):
		return self.__attr(Turtle.__resAttrib_y)
	@property
	def resolution_attribs(self):
		return (
			self.resolution_attrib_x,
			self.resolution_attrib_y
		)

	def bake_dir_abs_path(self):
		"""
		Absolute path to the directory used by current Turtle Bake node to bake to.

		:return: string
		"""
		from drl.for_maya import info

		proj_dir = info.get_project_dir()
		assert isinstance(proj_dir, _str_t)
		subpath = self.dir_attrib.get('')
		assert isinstance(subpath, _str_t)

		# extra '' forces trailing slash
		return os.path.join(proj_dir, subpath, '').replace('\\', '/')

	@staticmethod
	def is_bake():
		"""
		Whether current Turtle BakeSet node is in "bake" mode (not render).

		:return: bool
		"""
		tt_opt_node = pm.PyNode(Turtle.__turtleOptionsNode)
		bakeMode_attr = tt_opt_node.attr(Turtle.__turtleBakeModeAttr)
		assert isinstance(bakeMode_attr, pm.Attribute)
		return bakeMode_attr.get(0) == 1

	def pre_render(self):
		import time
		from drl_common import filesystem as fs

		if not Turtle.is_bake():
			return

		attr = self.dir_attrib
		postfix = Turtle.__drl_tmp_postfix
		new_val = os.path.join(attr.get(''), postfix).replace('\\', '/')
		attr.set(new_val)
		fs.clean_path_for_folder(self.bake_dir_abs_path(), overwrite=1)

		print('Waiting for %s seconds before starting render...' % sleep_time)
		time.sleep(sleep_time)

	@staticmethod
	def __dir_attr_with_removed_tmp(path_with_tmp=''):
		cur_dir = path_with_tmp
		postfix_len = Turtle.__drl_tmp_postfix_len
		if cur_dir[-postfix_len:] == Turtle.__drl_tmp_postfix:
			return cur_dir[:-postfix_len]
		return cur_dir

	def post_render(self):
		from drl_common import filesystem as fs
		import time

		if not Turtle.is_bake():
			return

		attr = self.dir_attrib
		new_val = Turtle.__dir_attr_with_removed_tmp(attr.get(''))
		dir_path = self.bake_dir_abs_path()
		if os.path.exists(dir_path) and os.path.isdir(dir_path) and not os.listdir(dir_path):
			fs.clean_path_for_file(dir_path, overwrite_folders=1, remove_file=1)
		attr.set(new_val)

		print('Waiting for %s seconds after render completion...' % sleep_time)
		time.sleep(sleep_time)

	def post_frame(self, del_exr=False):
		import time
		if not Turtle.is_bake():
			return

		print('Waiting for %s seconds before post-processing render...' % sleep_time)
		time.sleep(sleep_time)

		bake_dir = self.bake_dir_abs_path()
		filepaths = [
			os.path.join(bake_dir, x).replace('\\', '/')
			for x in os.listdir(bake_dir)
		]
		res = list()
		len_f = len(filepaths)
		for i, f in enumerate(filepaths):
			res_png = Turtle.postprocess_file_for_unity(
				f,
				Turtle.__dir_attr_with_removed_tmp(self.bake_dir_abs_path()),
				del_exr,
				self.__to_exr
			)
			if res_png:
				if not res:
					print('\n')
				res.append(res_png)
				print('Processed {cur} of {total}: "{path}"'.format(
					cur=1+i, total=len_f, path=res_png
				))
		if res:
			print('\nFinished!\n\n')

	@staticmethod
	def clean_filename(filename, shapes_to='Building', extra_replacements=None):
		"""
		Performs filename cleanup after Turtle's bake.
		Replaces long meaningless words to something more meaningful.
		:param filename: source filename (without extension or path)
		:param shapes_to: string, what to rename 'shapes' word to
		:param extra_replacements: list of tuples (zip) for replacement: (from, to)
		:return: string
		"""
		assert isinstance(filename, _str_t)
		replacements = [
			('tpIllumination', 'LM'),
			('Shape', ''),
			('shapes', shapes_to)
		]
		if extra_replacements:
			if not isinstance(extra_replacements, (list, tuple, set)):
				raise Exception('Wrong datatype for argument <extra_replacements>: ' + repr(extra_replacements))
			replacements.extend(extra_replacements)
		for rep in replacements:
			# filename = 'shapes_tpIllumination.3'
			filename = filename.replace(*rep)
		return filename

	@staticmethod
	def postprocess_file_for_unity(
		file_path='',
		move_to_folder_after_completion='',
		remove_src_tex=False,
		to_exr=False
	):
		"""
		Performs single-file post-processing after bake.
		Supposed to be used sequentially for all the directory contents.
		This directory is supposed to be temp, containing only baked EXRs.

		:param file_path: str, path of the file to post-process
		:param move_to_folder_after_completion: path to a folder where this file needs to be placed after conversion
		:param remove_src_tex: whether to remove source EXR
		:return: Filepath of resulting png if conversion was successful, None otherwise
		"""
		import time
		from drl_common import filesystem as fs
		from for_nuke import launch_nk_process as launch_nk
		import shutil

		if not file_path:
			raise Exception('File path is empty.')
		if not os.path.exists(file_path):
			raise Exception("File doesn't exist.")
		if not os.path.isfile(file_path):
			msg = '\nPost-processing works only with files. Folder provided: "%s"' % file_path
			wrn.warn(msg, RuntimeWarning, stacklevel=3)
			return None

		basename, ext = os.path.splitext(file_path)
		if ext.lower() != '.exr':
			msg = '\nOperation works only with EXR files. Ignored: "%s"' % file_path
			wrn.warn(msg, RuntimeWarning, stacklevel=3)
			return None

		folder, basename = os.path.split(basename)
		filename = Turtle.clean_filename(basename) + ('.exr' if to_exr else '.png')
		out_png_path = os.path.join(folder, filename).replace('\\', '/')

		# file_path = 'qqq'
		# out_png_path = 'wwwwww'
		# remove_src_tex = True
		print (
			"Call Nuke-processing function:\n"
			"for_nuke.launch_nk_process.process(\n"
			"\tr'{0}',\n"
			"\tr'{1}',\n"
			"\t{2}\n"
			")".format(
				file_path, out_png_path, remove_src_tex
			)
		)
		launch_nk.process(
			file_path, out_png_path, remove_src_tex
		)

		if move_to_folder_after_completion:
			moved_path = os.path.join(move_to_folder_after_completion, filename).replace('\\', '/')

			print(
				"Moving texture to new location:\n\t{0}\n\t->{1}".format(out_png_path, moved_path)
			)
			fs.clean_path_for_file(moved_path, overwrite_folders=1, remove_file=1)

			attempt = 1
			success = False
			start_attempt_time = dt.datetime.now()
			delta_time = dt.timedelta(0, 0, 0)
			max_delta = dt.timedelta(0, time_error_treshold)
			err_res = IOError()

			while not success and delta_time < max_delta:
				print("Attempt: " + str(attempt))
				next_attempt_time = dt.datetime.now()
				delta_time = next_attempt_time - start_attempt_time
				try:
					shutil.move(out_png_path, moved_path)
					success = True
				except IOError as err_in:
					err_res = err_in
					success = False
					time.sleep(sleep_time)
				attempt += 1

			if success:
				out_png_path = moved_path
				print("Successfully moved")
			else:
				raise err_res
		return out_png_path



class BakeSet(object):
	#region global default values
	__prefix = 'DRL_bakeSet_'
	__extra_postfix = '_extra'
	__common_name = 'DRL_bakeSet_common'
	__common_extra_postfix = '_comm'
	__default_res = 0
	__default_file = ''
	__default_directory = ''

	# __default_render_res = 512
	# __default_render_file = '$s_$p.$f.$e'
	# __default_render_directory = 'LightMaps/'

	__attrib_res_name_parent = 'resolution'
	__attrib_res_name_comps = ['x', 'y']
	__attrib_res_title = 'Texture Res'
	__attrib_directory_name = 'bake_directory'
	__attrib_directory_title = 'Directory'
	__attrib_file_name = 'bake_filename'
	__attrib_file_title = 'File Name'

	__prefix_len = len(__prefix)
	__extra_postfix_len = len(__extra_postfix)
	__attrib_res_names = [__attrib_res_name_parent + '_' + p.lower() for p in __attrib_res_name_comps]
	#endregion

	def __init__(self, obj, res=None, res_y=None, dir=None, filename=None, create_if_dont_exist=True):
		super(BakeSet, self).__init__()
		#region error-handling

		# an object passed in tuple or list:
		if isinstance(obj, (tuple, list)):
			if not obj:
				raise Exception('Zero-length list or tuple is given as <obj> argument.')
			if not len(obj) == 1:
				raise Exception('Multiple objects is given as <obj> argument. Cannot create multiple BakeSets at once.')
			obj = obj[0]

		# unexpected argument datatype:
		if not (
			obj is None or
			isinstance(obj, (pm.PyNode, _str, _unicode))
		):
			raise Exception('Wrong type for <obj> argument: ' + str(type(obj)))

		# null or empty string:
		if obj is None or (isinstance(obj, _str_t) and not obj):
			raise Exception('Empty <obj> is given of type: ' + str(type(obj)))

		#endregion
		# obj is guaranteed to be a PyNode or meaningful string

		#region create new set / rename existing
		proper_name = BakeSet.get_bake_set_name(obj)
		if BakeSet.is_common_set_name(obj) or BakeSet.is_common_set_name(proper_name):
			raise Exception('Unable to create BakeSet from common set.')

		if BakeSet.exists(proper_name):
			obj = pm.PyNode(proper_name)
		elif BakeSet.exists(obj) and not BakeSet.is_extra_set_name(obj):
			obj = pm.rename(obj, proper_name)
		else:
			# BakeSet doesn't exist
			if not create_if_dont_exist:
				raise Exception("Silent BakeSet creation is disabled, and given <obj> doesn't exist: " + repr(obj))
			obj = pm.sets(name=proper_name, empty=True)

		obj = BakeSet.assert_set_node(obj)
		#endregion
		# obj is guaranteed to be:
		# * a PyNode
		# * pointing to an existing object
		# * with proper BakeSet name

		self.__set_main_set_node(obj)
		self.__extra_node = False

		#region create attributes
		if res is None and res_y is None:
			a = self.res_attribs  # required to create attrib if doesn't exist
		else:
			self.set_resolution(res, res_y)

		if dir is None:
			a = self.directory_attrib
		else:
			self.directory_path = dir

		if filename is None:
			a = self.file_attrib
		else:
			self.file_name = filename
		#endregion

	@staticmethod
	def get_instance(bake_set=None):
		if bake_set is None or isinstance(bake_set, (pm.PyNode, _str, _unicode, list, tuple, set)):
			bake_set = BakeSet(bake_set)
		assert isinstance(bake_set, BakeSet)
		return bake_set

	@staticmethod
	def assert_set_node(node):
		assert isinstance(node, pm.PyNode)
		assert isinstance(node, pm.nodetypes.ObjectSet)
		return node

	#region list BakeSet nodes

	@staticmethod
	def all_scene_sets():
		"""
		Simple service method returning list of all the generic set nodes. No filtering.
		:return:
		"""
		return pm.ls(exactType='objectSet')

	@staticmethod
	def all_main_sets():
		return [x for x in BakeSet.all_scene_sets() if BakeSet.is_bake_set_name(x)]

	@staticmethod
	def all_extra_sets():
		return [x for x in BakeSet.all_scene_sets() if BakeSet.is_extra_set_name(x)]

	@staticmethod
	def all_common_extra_sets():
		return [x for x in BakeSet.all_scene_sets() if BakeSet.is_common_extra_set_name(x)]

	#endregion

	#region default values

	@staticmethod
	def default_resolution():
		return BakeSet.__default_res

	@staticmethod
	def default_file_name():
		return BakeSet.__default_file

	@staticmethod
	def default_directory():
		return BakeSet.__default_directory

	#endregion

	#region check or convert set type

	@staticmethod
	def exists(node):
		return ls.pymel.object_set_exists(node)

	@staticmethod
	def __get_node_name(node):
		return ls.pymel.short_item_name(node)

	@staticmethod
	def is_bake_set_name(node):
		"""
		Checks whether provided node has exactly BakeSet's name
		"""
		node = BakeSet.__get_node_name(node)
		pre = BakeSet.__prefix
		extra = BakeSet.__extra_postfix

		if(
			not node.startswith(pre) or
			node == pre or
			node.endswith(extra) or
			BakeSet.is_common_set_name(node) or
			BakeSet.is_common_extra_set_name(node)
		):
			return False

		return True

	@staticmethod
	def is_bake_set(node):
		"""
		Checks whether given node is 'objectSet' and has BakeSet's name.
		"""
		bs = BakeSet
		return bs.exists(node) and bs.is_bake_set_name(node)

	@staticmethod
	def is_extra_set_name(node):
		"""
		Checks whether provided node has exactly extra-set's name
		"""
		node = BakeSet.__get_node_name(node)
		pre = BakeSet.__prefix
		extra = BakeSet.__extra_postfix

		if(
			not node.startswith(pre) or
			not node.endswith(extra) or
			node == pre or
			node == extra or
			BakeSet.is_common_set_name(node) or
			BakeSet.is_common_extra_set_name(node)
		):
			return False

		return True

	@staticmethod
	def is_extra_set(node):
		"""
		Checks whether given node is 'objectSet' and has extra-set's name.
		"""
		bs = BakeSet
		return bs.exists(node) and bs.is_extra_set_name(node)

	@staticmethod
	def is_common_set_name(node):
		"""
		Checks whether provided node has common set's name.
		"""
		node = BakeSet.__get_node_name(node)
		return node == BakeSet.__common_name

	@staticmethod
	def is_common_set(node):
		"""
		Checks whether given node is 'objectSet' and has common set's name.
		"""
		bs = BakeSet
		return bs.exists(node) and bs.is_common_set_name(node)

	@staticmethod
	def is_common_extra_set_name(node):
		"""
		Checks whether provided node has common extra-set's name.
		"""
		node = BakeSet.__get_node_name(node)
		pre = BakeSet.__prefix
		post = BakeSet.__common_extra_postfix
		if(
			not node.startswith(pre) or
			not node.endswith(post) or
			node == pre or
			node == post or
			BakeSet.is_common_set_name(node)
		):
			return False

		return True

	@staticmethod
	def get_bake_set_name(node):
		"""
		Generates a proper name for BakeSet node.
		Adds prefix / removes postfix if necessary.
		"""
		node = BakeSet.__get_node_name(node)
		pre = BakeSet.__prefix
		extra = BakeSet.__extra_postfix
		extra_len = BakeSet.__extra_postfix_len

		if not node.startswith(pre):
			node = pre + node
		if node == pre:
			node += '1'  # ensure node has at least something in it's name
		if node.endswith(extra):
			node = node[:-extra_len]
		if node == BakeSet.common_set_name():
			node += '1'

		return node

	@staticmethod
	def get_extra_set_name(node):
		"""
		Generates a proper name for extra-set node.
		Adds prefix / postfix if necessary.
		"""
		return BakeSet.get_bake_set_name(node) + BakeSet.__extra_postfix

	@staticmethod
	def get_common_extra_set_name(node):
		"""
		Generates a proper name for extra-set node.
		Adds prefix / postfix if necessary.
		"""
		return BakeSet.get_bake_set_name(node) + BakeSet.__common_extra_postfix


	#endregion

	#region main node

	def __force_main_set_name(self):
		node = self.__set_node
		if not BakeSet.is_bake_set_name(node):
			pm.rename(node, BakeSet.get_bake_set_name(node))

	def __set_main_set_node(self, node):
		if pm.nodeType(node) != 'objectSet':
			raise Exception('The given object is not Maya Set: ' + node)
		if not isinstance(node, pm.PyNode):
			node = pm.PyNode(node)
		node = BakeSet.assert_set_node(node)
		self.__set_node = node
		self.__force_main_set_name()

	@property
	def node(self):
		n = self.__set_node
		n = BakeSet.assert_set_node(n)
		self.__force_main_set_name()
		return n
	@node.setter
	def node(self, value):
		self.__set_main_set_node(value)

	@property
	def objects(self):
		return self.node.members()
	@objects.setter
	def objects(self, value):
		self.node.resetTo(value)
	#endregion

	#region extra node

	def get_extra_node(self, create_if_none=False):
		node = self.__extra_node
		extra_name = BakeSet.get_extra_set_name(self.node)
		if not node:
			if BakeSet.exists(extra_name):
				node = pm.PyNode(extra_name)
			else:
				if not create_if_none:
					return None
				else:
					node = pm.sets(name=extra_name, empty=True)
		elif node.name() != extra_name:
			pm.rename(node, extra_name)
		node = BakeSet.assert_set_node(node)
		self.__extra_node = node
		return node

	@property
	def extra_node(self):
		return self.get_extra_node(True)

	@property
	def extra_objects(self):
		extra = self.get_extra_node()
		if not extra:
			return []
		return extra.members()
	@extra_objects.setter
	def extra_objects(self, value):
		assert isinstance(value, (pm.PyNode, _str, _unicode, list, tuple, set))
		extra = self.get_extra_node(False)
		if not extra:
			if not value:
				return
			extra = self.get_extra_node(True)
		extra.resetTo(value)

	#endregion

	#region common node

	@staticmethod
	def common_set_name():
		"""
		Returns common set's name.
		"""
		return BakeSet.__common_name

	@staticmethod
	def common_set_exists():
		return BakeSet.exists(BakeSet.common_set_name())

	@staticmethod
	def common_set():
		"""
		Returns common set's PyNode. Creates it if necessary.
		:return:
		"""
		comm_nm = BakeSet.common_set_name()
		if BakeSet.exists(comm_nm):
			node = pm.PyNode(comm_nm)
		elif pm.objExists(comm_nm):
			# there is an object with this name, but it's not a set:
			new_name = comm_nm + '1'
			for o in pm.ls(comm_nm):
				if pm.nodeType(o) == 'objectSet' and BakeSet.__get_node_name(o) == comm_nm:
					node = o
					break
				pm.rename(o, new_name)
			node = pm.sets(name=comm_nm, empty=True)
		else:
			# set doesn't exist:
			node = pm.sets(name=comm_nm, empty=True)
		node = BakeSet.assert_set_node(node)
		return node

	#endregion

	#region common extra nodes

	# @staticmethod
	# def is_common_extra_set(node):
	# 	"""
	# 	Checks whether given node is 'objectSet' and has common extra-set's name.
	# 	"""
	# 	bs = BakeSet
	# 	return bs.exists(node) and bs.is_common_extra_set_name(node)

	def is_common_extra_set(self, node):
		"""
		Checks whether provided node fits to be current BakeSet's common extra node.
		"""
		node = BakeSet.__get_node_name(node)
		post = BakeSet.__common_extra_postfix
		if not node.endswith(post):
			return False
		# node = 'Barracks1_2' + post
		extra_start = node[:-len(post)]
		if not extra_start or not extra_start.startswith(BakeSet.__prefix):
			return False

		main_name = self.node.name()
		assert isinstance(main_name, _str_t)
		return main_name.startswith(extra_start)

	def common_extra_nodes(self):
		return [x for x in BakeSet.all_scene_sets() if self.is_common_extra_set(x)]

	def common_extra_objects(self):
		objs = list()
		for es in self.common_extra_nodes():
			es = BakeSet.assert_set_node(es)
			objs.extend(es.members())
		return objs

	#endregion

	#region resolution attributes

	def __forced_delete_attrib(self, attr_name):
		assert isinstance(attr_name, _str_t)
		node = self.node
		if node.hasAttr(attr_name):
			node.attr(attr_name).delete()

	def has_res_attrib(self):
		'''
		Whether BakeSet node has required resolution attributes.
		:return: True/False
		'''
		node = self.node
		atr_names = BakeSet.__attrib_res_names
		return node.hasAttr(atr_names[0]) and node.hasAttr(atr_names[1])

	def add_res_attrib(self):
		'''
		Forcefully adds resolution attributes with default values.
		As a first step, deletes existing res attrib, if it exists.
		:return: pm.Attribute: (res_x, res_y)
		'''
		node = self.node
		attr_nm = BakeSet.__attrib_res_name_parent
		atr_names = BakeSet.__attrib_res_names
		# attr_nm = 'res'
		# atr_names = ['res_x', 'res_y']

		for a in [attr_nm] + atr_names:
			self.__forced_delete_attrib(a)

		pm.addAttr(
			node, at='short2',
			ln=attr_nm, nn=BakeSet.__attrib_res_title,
			writable=True,
			keyable=True
		)
		for i in xrange(2):
			pm.addAttr(
				node, parent=attr_nm, at='short',
				ln=atr_names[i],
				nn=BakeSet.__attrib_res_name_comps[i].upper(),
				min=0, hasMinValue=True,
				writable=True,
				keyable=True,
				dv=BakeSet.__default_res  # default value
			)
		return node.attr(atr_names[0]), node.attr(atr_names[1])

	@property
	def res_attribs(self):
		'''
		A tuple of two attributes defining the resolution.
		:return: pm.Attribute: (res_x, res_y)
		'''
		if not self.has_res_attrib():
			return self.add_res_attrib()
		node = self.node
		atr_names = BakeSet.__attrib_res_names
		attribs = (
			node.attr(atr_names[0]),
			node.attr(atr_names[1])
		)
		assert isinstance(attribs[0], pm.Attribute)
		assert isinstance(attribs[1], pm.Attribute)
		return attribs

	@property
	def res_x_attrib(self):
		a = self.res_attribs[0]
		assert isinstance(a, pm.Attribute)
		return a

	@property
	def res_y_attrib(self):
		a = self.res_attribs[1]
		assert isinstance(a, pm.Attribute)
		return a

	#endregion

	#region resolution values

	@staticmethod
	def __get_res_from_args(res=None, res_y=None):
		'''
		Converts 2 optional arguments to a consistent tuple of resolutions.
		:return: (res_x, res_y)
		'''
		assert (
			isinstance(res, (type(None), int)) and
			isinstance(res_y, (type(None), int))
		)

		if isinstance(res, int) and isinstance(res_y, int):
			# both arguments provided - separate x/y mode
			return res, res_y
		elif isinstance(res, int):
			# one argument provided - square resolution
			return res, res

		def_res = BakeSet.__default_res
		return def_res, def_res

	def set_resolution(self, res=None, res_y=None):
		'''
		Sets resolution width/height attributes. Creates them if they don't exist.
		:return:
		'''
		values = BakeSet.__get_res_from_args(res, res_y)
		for a, val in zip(self.res_attribs, values):
			a.set(val)

	@property
	def res(self):
		attribs = self.res_attribs
		return (
			attribs[0].get(),
			attribs[1].get()
		)
	@res.setter
	def res(self, value):
		assert isinstance(value, (list, tuple, int))
		if isinstance(value, int):
			self.set_resolution(value)
			return
		self.set_resolution(*value)

	@property
	def res_x(self):
		return self.res_x_attrib.get()
	@res_x.setter
	def res_x(self, value):
		assert isinstance(value, int)
		res_y = self.res_y_attrib.get()
		self.set_resolution(value, res_y)

	@property
	def res_y(self):
		return self.res_y_attrib.get()
	@res_y.setter
	def res_y(self, value):
		assert isinstance(value, int)
		res_x = self.res_x_attrib.get()
		self.set_resolution(res_x, value)

	#endregion

	#region texture attributes

	def has_file_attrib(self):
		return self.node.hasAttr(BakeSet.__attrib_file_name)

	def has_directory_attrib(self):
		return self.node.hasAttr(BakeSet.__attrib_directory_name)

	def __add_string_attrib(self, attr_name, lable='', default_value=''):
		assert isinstance(attr_name, _str_t)
		assert isinstance(lable, _str_t)
		assert isinstance(default_value, _str_t)
		if not lable:
			lable = attr_name
		node = self.node
		self.__forced_delete_attrib(attr_name)

		pm.addAttr(
			node, dt='string',
			ln=attr_name,
			nn=lable,
			writable=True,
			keyable=True
		)
		a = node.attr(attr_name)
		assert isinstance(a, pm.Attribute)

		if default_value:
			a.set(default_value)

		return a

	def add_file_attrib(self):
		return self.__add_string_attrib(
			BakeSet.__attrib_file_name,
			BakeSet.__attrib_file_title,
			BakeSet.__default_file
		)

	def add_directory_attrib(self):
		return self.__add_string_attrib(
			BakeSet.__attrib_directory_name,
			BakeSet.__attrib_directory_title,
			BakeSet.__default_directory
		)

	@property
	def file_attrib(self):
		if not self.has_file_attrib():
			return self.add_file_attrib()
		a = self.node.attr(BakeSet.__attrib_file_name)
		assert isinstance(a, pm.Attribute)
		return a

	@property
	def directory_attrib(self):
		if not self.has_directory_attrib():
			return self.add_directory_attrib()
		a = self.node.attr(BakeSet.__attrib_directory_name)
		assert isinstance(a, pm.Attribute)
		return a

	#endregion

	#region texture values

	@property
	def file_name(self):
		return self.file_attrib.get()
	@file_name.setter
	def file_name(self, value):
		assert isinstance(value, _str_t)
		self.file_attrib.set(value)

	@property
	def directory_path(self):
		return self.directory_attrib.get()
	@directory_path.setter
	def directory_path(self, value):
		assert isinstance(value, _str_t)
		self.directory_attrib.set(value)

	#endregion

	#region user-friendly high-level methods to add objects to sets from selection

	@staticmethod
	def __find_common_parent_path(objs):
		'''
		Finds the lowest possible common to_parent node for the list of nodes.
		Returns:
			* full path to a to_parent node if common one is found.
			* empty string otherwise
		:param objs: list/tuple of strings/PyNodes
		:return: string
		'''
		from maya import cmds
		assert isinstance(objs, (list, tuple))

		if not objs:
			raise Exception('No objects provided.')
		if len(objs) == 1:
			obj = objs[0]
			parent_list = pm.listRelatives(objs[0], parent=True)
			parent = parent_list[0] if parent_list else ''
			return parent

		# list of strings, short names:
		ful_paths = [x.name() if isinstance(x, pm.PyNode) else x for x in objs]
		# full paths, limited to objects only:
		ful_paths = cmds.ls(ful_paths, long=True, objectsOnly=True)
		ful_paths = [('|' + x.strip('|')) for x in ful_paths]
		prefix = os.path.commonprefix(ful_paths)
		prefix = prefix.split('|')
		if prefix[-1]:
			prefix.pop()
		return '|'.join(prefix).rstrip('|_')

	def common_group_name(self, short_name=False):
		"""
		Returns:
			* name of to_parent group containing all the BakeSet objects (if there is one)
			* empty string if there's no common group
		:return: string (shortest unique by default, can be changed to short by argument)
		"""
		objs = self.objects
		if not objs:
			return ''
		common_full = BakeSet.__find_common_parent_path(objs)
		if not common_full:
			return ''
		name = pm.PyNode(common_full).name()
		if short_name:
			name = BakeSet.__get_node_name(name)
		return name

	@staticmethod
	def __add_objects_to_set_error_handle(objs=None, selection_if_none=True):
		'''
		Performs error-checks and returns objects as a list. Reult is guaranteed to:
		* be a list or tuple
		* contains either one non-ObjectSet obj, or multiple objs
		:return: list or tuple (in case source provided as tuple)
		'''
		if objs is None:
			if not selection_if_none:
				raise Exception("Selection isn't used, and no object is provided.")
			objs = pm.ls(sl=True)

		if isinstance(objs, (pm.PyNode, _str, _unicode)):
			if not objs:
				raise Exception('Empty object is given.')
			objs = [objs]
		assert isinstance(objs, (list, tuple))

		if not objs:
			raise Exception('No objects provided.')
		# objs are guaranteed to be a list or tuple with at least 1 element.
		# Probably with PyNodes or strings.

		if len(objs) == 1 and BakeSet.exists(objs[0]):
			raise Exception('At least one object is expected. Only set provided: ' + repr(objs[0]))
		# now ^ there should be either multiple object, or one non-ObjectSet obj
		return objs

	@staticmethod
	def __add_objects_to_set_get_proper_set_and_objs(objs=None, selection_if_none=True):
		objs = BakeSet.__add_objects_to_set_error_handle(objs, selection_if_none)

		if BakeSet.exists(objs[-1]):
			# special case: last node is ObjectSet manually specified to become BakeSet
			obj_set = objs.pop()
		else:
			# default behavior: last node isn't a resulting set, just plain objs list
			common_parent = BakeSet.__find_common_parent_path(objs)
			# generate basic name for new set:
			if common_parent:
				obj_set = pm.PyNode(common_parent).name()
				obj_set = BakeSet.__get_node_name(obj_set)
			else:
				obj_set = '1'

			set_name = BakeSet.get_bake_set_name(obj_set)
			if BakeSet.exists(set_name):
				# in case we didn't select a set manually,
				# and common-name set for current objects already exists,
				# we need to create a new one:
				obj_set = pm.sets(name=set_name, empty=True)

		obj_set = BakeSet(obj_set)
		return obj_set, objs

	@staticmethod
	def add_objects_to_set(objs=None, selection_if_none=True):
		'''
		High-level static method, allowing to easily
		* create new BakeSets from selected objects
		* add selected objects to selected set (if it's selected last)
		:param objs:
		:param selection_if_none: bool, whether to use current selection if None provided
		:return: resulting BakeSet class instance
		'''
		obj_set, objs = \
			BakeSet.__add_objects_to_set_get_proper_set_and_objs(objs, selection_if_none)
		obj_set.node.addMembers(objs)
		assert isinstance(obj_set, BakeSet)
		return obj_set

	@staticmethod
	def add_objects_to_set_with_postfix(postfix, objs=None, selection_if_none=True):
		assert isinstance(postfix, _str_t)
		if not postfix:
			raise Exception('No <postfix> is provided.')
		bs = BakeSet.add_objects_to_set(objs, selection_if_none)
		bs_node = bs.node
		new_name = BakeSet.__get_node_name(bs_node.name()) + postfix
		pm.rename(bs_node, new_name)
		return bs

	@staticmethod
	def add_objects_to_extra_set(objs=None, selection_if_none=True):
		'''
		High-level static method, allowing to easily add objects to an extra set:
		* creates new BakeSet if it doesn't exist
		* creates extra set if it doesn't exist
		* adds selected objects to an existing extra set
			(if either this set or it's corresponding BakeSet is selected last)
		:param objs:
		:param selection_if_none: bool, whether to use current selection if None provided
		:return: resulting BakeSet class instance (not extra-set itself)
		'''
		obj_set, objs = \
			BakeSet.__add_objects_to_set_get_proper_set_and_objs(objs, selection_if_none)
		obj_set.extra_node.addMembers(objs)
		assert isinstance(obj_set, BakeSet)
		return obj_set

	@staticmethod
	def get_common_set_objects():
		if not BakeSet.common_set_exists():
			return []
		return BakeSet.common_set().members()

	@staticmethod
	def set_common_set_objects(objs):
		return BakeSet.common_set().resetTo(objs)

	@property
	def common_objects(self):
		return BakeSet.get_common_set_objects()
	@common_objects.setter
	def common_objects(self, value):
		BakeSet.set_common_set_objects(value)

	@staticmethod
	def add_objects_to_common_set(objs=None, selection_if_none=True):
		objs = BakeSet.__add_objects_to_set_error_handle(objs, selection_if_none)
		node = BakeSet.common_set()
		node.addMembers(objs)
		return node

	@staticmethod
	def add_objects_to_common_extra_set(objs=None, selection_if_none=True):
		def get_proper_set_and_objs(objs=None, selection_if_none=True):
			objs = BakeSet.__add_objects_to_set_error_handle(objs, selection_if_none)

			if BakeSet.exists(objs[-1]):
				# special case: last node is ObjectSet manually specified to become BakeSet
				obj_set = objs.pop()
				obj_set = BakeSet.__get_node_name(obj_set)
			else:
				# default behavior: last node isn't a resulting set, just plain objs list
				common_parent = BakeSet.__find_common_parent_path(objs)
				# generate basic name for new set:
				if common_parent:
					obj_set = pm.PyNode(common_parent).name()
					obj_set = BakeSet.__get_node_name(obj_set)
				else:
					obj_set = '1'

			set_name = BakeSet.get_common_extra_set_name(obj_set)
			obj_set = pm.sets(name=set_name, empty=True)
			obj_set = BakeSet.assert_set_node(obj_set)

			return obj_set, objs

		ex_set, objs = get_proper_set_and_objs(objs, selection_if_none)
		ex_set.addMembers(objs)
		return ex_set

	#endregion



class Sequence(object):
	__default_res = 512
	__default_file = '$s_$p.$f.$e'
	__default_directory = 'LightMaps/'
	__default_frame_range = [0, 3]
	bs = BakeSet

	def __init__(self):
		super(Sequence, self).__init__()

	@staticmethod
	def bake_sets():
		def sorting_f(set_obj):
			def do_replace(src, from_str, to_str):
				assert isinstance(src, _str_t)
				assert isinstance(from_str, _str_t)
				assert isinstance(to_str, _str_t)
				if src.endswith(from_str):
					src = src[:-len(from_str)] + to_str
				return src

			set_obj = BakeSet.assert_set_node(set_obj)
			key = set_obj.name()
			assert isinstance(key, _str_t)
			key = key.lower()

			reps = [
				('_bld', '_aaaaa'),
				('_gnd', '_aabbb')
			]
			for r in reps:
				key = do_replace(key, *r)

			return key

		all_sets = pm.ls(exactType='objectSet')
		res = [x for x in all_sets if BakeSet.is_bake_set_name(x)]
		res.sort(key=sorting_f)
		return res

	@staticmethod
	def isolate_bake_set(bake_set):
		"""
		Forces the only visible objects to be current bakeSet's ones.
		:param bake_set: BakeSet to show
		:return: list of hidden objects
		"""
		from drl.for_maya import ls
		bake_set = BakeSet.get_instance(bake_set)

		vis_objs = (
			bake_set.objects +
			bake_set.extra_objects +
			bake_set.common_objects +
			bake_set.common_extra_objects()
		)
		all_objs = ls.pymel.all_objects()
		hidden_objs = pm.ls(invisible=True, dag=True)
		vis_children = pm.listRelatives(vis_objs, allDescendents=True) + vis_objs
		# manually get the objects that will be unhidden anyway (to keep track of them):
		vis_parents = ls.pymel.all_parents(vis_objs, False)
		to_hide = [
			x for x in all_objs if not (
				x in set(hidden_objs + vis_children + vis_parents)
			)
		]
		pm.hide(to_hide)
		pm.showHidden(vis_objs, above=True)
		return to_hide

	@staticmethod
	def get_default_render_values():
		"""
		Returns default bakeSet's values.
		:return: res, file_name, directory
		"""
		bs = BakeSet
		return (
			bs.default_resolution(),
			bs.default_file_name(),
			bs.default_directory()
		)

	@staticmethod
	def set_render_values(res_x, res_y, file_name, directory, turtle_node=None):
		from pprint import pprint as pp
		# res_x, res_y, file_name, directory = (64, 64, u'$s_$p.$f.$e', u'LightMaps/Barracks/qqq/')
		# pp([res_x, res_y, file_name, directory, turtle_node])
		ttl = Turtle.get_instance(turtle_node)
		ttl.resolution_attrib_x.set(res_x)
		ttl.resolution_attrib_y.set(res_y)
		ttl.filename_attrib.set(file_name)
		ttl.dir_attrib.set(directory)

	@staticmethod
	def get_render_values_from_bake_set(bake_set):
		"""
		Returns current bakeSet's values.
		:return: res_x, res_y, file_name, directory
		"""
		bake_set = BakeSet.get_instance(bake_set)
		res_x, res_y = bake_set.res
		return res_x, res_y, bake_set.file_name, bake_set.directory_path

	@staticmethod
	def get_render_values(turtle_node=None):
		"""
		Returns global Turtle's values.
		:return: res_x, res_y, file_name, directory
		"""
		ttl = Turtle.get_instance(turtle_node)
		return (
			ttl.resolution_attrib_x.get(),
			ttl.resolution_attrib_y.get(),
			ttl.filename_attrib.get(),
			ttl.dir_attrib.get()
		)

	@staticmethod
	def get_directory_from_objects_group(bake_set):
		"""
		Generates directory path based on BakeSet's objects and their containing group.
		:param bake_set:
		:return: string
		"""
		import re
		bake_set = BakeSet.get_instance(bake_set)

		group_name = bake_set.common_group_name(True)
		if group_name:
			# group_name = 'Barracks_1_2_q_1-3_'
			source_name = group_name
			nums = ''
			match_obj = re.search('([0-9_-]+)$', group_name)
			if match_obj:
				nums = match_obj.groups()[-1]
				assert isinstance(nums, _str_t)
				# group_name = '--_--Barracks_1_2_q_1-3_--_'
				group_name = group_name[:-len(nums)]
				nums = nums.replace('_', '-').strip('-')
			group_name = group_name.strip('_-')
			if nums:
				group_name = '/'.join([group_name, nums])
			else:
				group_name = '/'.join([group_name, source_name[len(group_name):]])
			directory = group_name
		else:
			directory = ''
		directory = directory.strip('/')
		if directory:
			directory += '/'
		directory = Sequence.__default_directory + directory
		return directory

	@staticmethod
	def set_render_values_from_bake_set(bake_set, turtle_node=None, dir_from_parent_group=True):
		"""
		Sets Turtle's values to the ones from BakeSet.
		Returns the tuple of values that were in Turtle node before this operation.
		:param bake_set: BakeSet class instance.
		:param turtle_node: Turtle's layer node. None for default one.
		:param dir_from_parent_group: Whether to generate dir path from objects' group.
		:return: previous settings: res_x, res_y, file_name, directory
		"""
		assert isinstance(bake_set, BakeSet)
		ttl = Turtle.get_instance(turtle_node)
		bake_set = BakeSet.get_instance(bake_set)

		res_x, res_y, file_name, directory = Sequence.get_render_values_from_bake_set(bake_set)
		render_res_x, render_res_y, render_file, render_dir = Sequence.get_render_values(ttl)
		def_res, def_file, def_dir = Sequence.get_default_render_values()

		if res_x == def_res or res_x < 1:
			res_x = render_res_x
		if res_x < 2:
			res_x = Sequence.__default_res

		if res_y == def_res or res_y < 1:
			res_y = render_res_y
		if res_y < 2:
			res_y = Sequence.__default_res

		if file_name == def_file or not file_name:
			file_name = render_file
		assert isinstance(file_name, _str_t)
		if not file_name.endswith('.$e'):
			file_name = Sequence.__default_file

		dir_from_group = Sequence.get_directory_from_objects_group(bake_set)
		if not directory or not directory.strip('/\\') or directory == def_dir:
			directory = dir_from_group if dir_from_parent_group else render_dir
		if not directory or not directory.strip('/\\'):
			directory = (
				dir_from_group if dir_from_parent_group
				else Sequence.__default_directory
			)

		ttl.resolution_attrib_x.set(res_x)
		ttl.resolution_attrib_y.set(res_y)
		ttl.filename_attrib.set(file_name)
		ttl.dir_attrib.set(directory)

		return render_res_x, render_res_y, render_file, render_dir

	@staticmethod
	def render_bake_set_with_function(
		render_function,
		bake_set=None, turtle_node=None,
		dir_from_parent_group=True,
		selection_if_none=True,
		to_exr=False
	):
		"""
		Performs all the setup stuff before and after rendering a bake set,
		but the actual render command is specified with a given function.

		:param render_function: function performing the actual render command
		:param bake_set: BakeSet node to render
		:param turtle_node: Turtle node to render with
		:param dir_from_parent_group: whether to generate folder name from common group of rendered objects
		:param selection_if_none: if True and <bake_set> is None, selected set is used
		"""
		def handle_bs_arg_and_sel(bake_set=None, selection_if_none=True):
			"""
			Handles input BakeSet argument

			:return: BakeSet, is from selection, selection (list)
			"""
			pre_sel = pm.ls(sl=True)
			from_sel = False

			if bake_set is None and selection_if_none:
				if not pre_sel:
					raise Exception('Nothing selected')
				sel = pre_sel[0]
				if not BakeSet.is_bake_set(sel):
					raise Exception('Selected object is not a BakeSet')
				bake_set = sel
				from_sel = True

			bake_set = BakeSet.get_instance(bake_set)
			return bake_set, from_sel, pre_sel

		if not hasattr(render_function, '__call__'):
			raise Exception('No render function provided')

		bake_set, from_sel, pre_sel = handle_bs_arg_and_sel(bake_set, selection_if_none)
		hidden = Sequence.isolate_bake_set(bake_set)
		prev_values = Sequence.set_render_values_from_bake_set(bake_set, turtle_node, dir_from_parent_group)

		pm.select(bake_set.objects, r=True)
		render_function()

		# for some weird reason, assertion error appears if we re-set render values first.
		# so, to kinda avoid it, we're first un-hiding previously hidden:
		if hidden:
			pm.showHidden(hidden)

		Sequence.set_render_values(*prev_values, turtle_node=turtle_node)
		if pre_sel and not from_sel:
			pm.select(pre_sel, r=True)
		else:
			pm.select(cl=True)

	@staticmethod
	def render_bake_set_frame(
		bake_set=None, turtle_node=None,
		dir_from_parent_group=True,
		selection_if_none=True,
		to_exr=False
	):
		Sequence.render_bake_set_with_function(
			BatchRender.render_current_frame,
			bake_set, turtle_node, dir_from_parent_group, selection_if_none, to_exr
		)

	@staticmethod
	def render_bake_set(
		bake_set=None, turtle_node=None,
		dir_from_parent_group=True,
		frames=None,
		selection_if_none=True
	):
		def handle_frames_arg(frames=None):
			if isinstance(frames, (int, float)):
				frames = [frames]
			if not frames:
				return Sequence.__default_frame_range

			if isinstance(frames, tuple):
				frames = list(frames)
			if not isinstance(frames, list):
				raise Exception('List of size 2 is expected as <frames> argument. Got: ' + repr(frames))
			if len(frames) > 2:
				raise Exception('Wrong number of items in <frames> argument. 2 expected. Got: ' + repr(frames))
			elif len(frames) == 1:
				frames = [frames[0], frames[0]]
			assert len(frames) == 2
			return frames

		frames = handle_frames_arg(frames)

		def render_f():
			BatchRender(*frames).render_range()

		Sequence.render_bake_set_with_function(
			render_f, bake_set, turtle_node, dir_from_parent_group, selection_if_none
		)

	@staticmethod
	def render_all_bake_sets(turtle_node=None, dir_from_parent_group=True, frames=None):
		from pprint import pprint as pp
		bake_sets = Sequence.bake_sets()
		print('\n\n\n\n\t\tSets to render:')
		pp(bake_sets)
		for bs in bake_sets:
			Sequence.render_bake_set(bs, turtle_node, dir_from_parent_group, frames, False)
