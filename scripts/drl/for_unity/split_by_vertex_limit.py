from drl_common import errors as err

__author__ = 'DRL'

from maya import cmds
import warnings as wrn

from drl_common.py_2_3 import (
	str_t as _str_t,
	str_h as _str_h,
	t_strict_str as _str,
	t_strict_unicode as _unicode,
)
from ..for_maya import ls
from ..for_maya.geo.components.old.vertices import calc_unityCount as calc_vert
from ..for_maya import transformations as tr
from ..for_maya import utils as mu

hrc = ls.convert.hierarchy
no_sel = dict(selection_if_empty=False)



class CountedShape(object):
	def __init__(self, shapePath=None):
		self.__shape = ''
		self.__verts = 0
		self.__perform_error_check = True
		self.set_shape(shapePath)

	def __error_check_shape(self, shapePath):
		"""
		Performs error-check for the given shape to make sure it can be passed further as valid string argument.
		:param shapePath:
		:return: The shapePath argument, fixed to proper type if required and possible
		"""
		if self.__perform_error_check:
			if shapePath is None:
				raise Exception('CountedShape.set_shape(): Shape is not provided')
			elif isinstance(shapePath, (list, tuple)):
				shapePath = shapePath[0]
				msg = '\nList or tuple provided instead of string. Extracting 1st element: "%s"' % shapePath
				wrn.warn(msg, RuntimeWarning, stacklevel=3)
			elif isinstance(shapePath, set):
				raise Exception('CountedShape.set_shape(): Set provided instead of string')

			if isinstance(shapePath, _str_t):
				if shapePath == '':
					raise Exception('CountedShape.set_shape(): Empty string is given')
				# make sure this shape actually exist:
				elif not cmds.ls(shapePath):
					raise Exception("CountedShape.set_shape(): Provided object doesn't exist in the scene")
				# ... and that it is a polygonal shape:
				elif not cmds.ls(shapePath, type='mesh'):
					raise Exception("CountedShape.set_shape(): Provided object is not a polygonal shape node")
			else:
				raise Exception('CountedShape.set_shape(): Wrong argument type, string expected')
		return shapePath

	@property
	def shape(self):
		return self.__shape
	@shape.setter
	def shape(self, nuVal):
		msg = "\nIt's recommended to use set_shape() method instead of directly setting a value of <shape> parameter."
		wrn.warn(msg, RuntimeWarning, stacklevel=3)
		self.set_shape(nuVal)
	@shape.deleter
	def shape(self):
		raise Exception ('<shape> parameter cannot be deleted.')

	def set_shape(self, shapePath=None, calc_vertices=True):
		"""
		Specifies the shape of a CountedShape object.
		Also performs all the error-checks to make sure the given argument is existing polygonal shape node.
		Finally, calculates current vertex count for the shape.
		:param shapePath: path to the polygonal shape node
		:param calc_vertices: when off, disables (normally required) calculation of vertex count
		:return: None
		"""
		self.__perform_error_check = True  # make sure we'll error-check given path
		self.__shape = self.__error_check_shape(shapePath)
		if calc_vertices:
			self.__perform_error_check = False  # we've already checked it, no need to do it again
			self.__calc()
			self.__perform_error_check = True   # ... but turn it back on for the future

	def vertices(self, refresh=True):
		"""
		Returns the calculated number of vertices for the CountedShape.
		:param refresh: If set to False, skips re-calculation of vertices and returns cached value.
		:return: Integer number of vertices
		"""
		if refresh: self.__calc()
		return self.__verts

	def __calc(self):
		"""
		Updates the number of vertices for the shape object.
		:return: Also returns the result
		"""
		self.__verts = calc_vert(self.__error_check_shape(self.shape))
		return self.__verts

	def __repr__(self):
		return '< CountedShape: "%s", %d vertices >' % (self.shape, self.__verts)

	def __str__(self):
		return self.__repr__()

	def __call__(self, *args, **kwargs):
		return self.shape, self.__verts



class ShapesGroup(object):
	def __init__(self, name=None, items=None):
		self.__name = ''
		self.__items = list()
		if not name is None: self.name = name
		if not items is None: self.items = items

	def find_shape(self, shape):
		if not isinstance(shape, (CountedShape, _str, _unicode)):
			raise Exception('ShapesGroup.find_shape: string expected, received: %s' % shape)
		if isinstance(shape, CountedShape):
			shape = shape.shape
		for i in self.__items:
			if shape == i.shape: return i
		return None

	def add_shape(self, shape):
		if isinstance(shape, (list, set, tuple)):
			if not isinstance(shape, list):
				shape = list(shape)
			for s in shape: self.add_shape(s)
			return
		if isinstance(shape, _str_t):
			shape = CountedShape(shape)
		elif not isinstance(shape, CountedShape):
			raise Exception('ShapesGroup.add_shape: attempt to add an item of wrong type: %s' % shape)
		already_existing = self.find_shape(shape.shape)
		if already_existing is None:
			self.__items.append(shape)
		else:
			msg = '\nShapesGroup.add_shape: attempt to add already existing item:\n%s\n' % already_existing
			msg += 'Refreshing number of vertices: %d' % already_existing.vertices()
			wrn.warn(msg, RuntimeWarning, stacklevel=3)

	def remove_shape(self, shape):
		if isinstance(shape, (list, set, tuple)):
			if not isinstance(shape, list):
				shape = list(shape)
			for s in shape: self.remove_shape(s)
			return
		# fast operation for exact match of an object:
		while shape in self.__items:
			self.__items.remove(shape)
		# remove by shape path in the rest of cases:
		if isinstance(shape, CountedShape):
			shape = shape.shape
		elif not isinstance(shape, _str_t):
			raise Exception('ShapesGroup.remove_shape: a wrong type is provided: %s' % shape)
		# make sure we delete all occurances even if they somehow got in the list:
		while shape in [x.shape for x in self.__items]:
			found = self.find_shape(shape)
			self.__items.remove(found)

	def length(self):
		return len(self.__items)

	@property
	def name(self):
		return self.__name
	@name.setter
	def name(self, value):
		if not isinstance(value, (_str, _unicode, int)):
			raise Exception('ShapesGroup.name can only be a string or int.')
		self.__name = value
	@name.deleter
	def name(self):
		raise Exception('ShapesGroup.name cannot be deleted.')

	@property
	def items(self):
		return self.__items[:]
	@items.setter
	def items(self, value):
		if not isinstance(value, (list, set, tuple, _str, _unicode, CountedShape)):
			raise Exception('ShapesGroup.items: a wrong type is provided: %s' % value)
		self.__items = list()
		self.add_shape(value)
	@items.deleter
	def items(self):
		raise Exception('ShapesGroup.items cannot be deleted.')

	def __repr__(self):
		msg = 'empty '
		length = self.length()
		if length > 0:
			msg = '%d items:\n' % length
			msg += '\n'.join(['\t%s' % x for x in self.__items])
			msg += '\n'
		return '< ShapesGroup: "%s", %s>' % (self.name, msg)

	def __str__(self):
		return self.__repr__()

	def __call__(self, *args, **kwargs):
		return self.name, self.__items[:]



class GroupedShapes(object):
	class __ErrorGroup(object):
		def __init__(self):
			self.mat = ShapesGroup('caused by material')
			self.big = ShapesGroup('objects out of limit')
		def __repr__(self):
			return '< GroupedShapes.__ErrorGroup:\n%s,\n%s\n>' % (repr(self.mat), repr(self.big))
		def __str__(self):
			return self.__repr__()
		def __call__(self, *args, **kwargs):
			return self.mat, self.big

	def __init__(self, shapes=None, max_verts=300):
		self.__max = 300
		self.__unordered = ShapesGroup()
		self.__by_mat = list()
		self.__errored = self.__ErrorGroup()
		self.__parts = list()
		self.max_vert = max_verts
		self.unordered = shapes

	def __find_mat_group(self, mat):
		mat_groups = self.__by_mat
		for mg in mat_groups:
			if not isinstance(mg, ShapesGroup):
				raise Exception('GroupedShapes: Somehow non-ShapesGroup element appeared in groups by material: %s' % mg)
			if mg.name == mat:
				return mg
		return None

	def __add_to_mat_group(self, mat, shape):
		mat_gr = self.__find_mat_group(mat)
		if mat_gr is None:
			mat_gr = ShapesGroup(mat)
			self.__by_mat.append(mat_gr)
		mat_gr.add_shape(shape)
		for mg in self.__by_mat:
			if mg.name != mat: mg.remove_shape(shape)

	def __rebuild_from_matgroups(self):
		self.__parts = list()
		for mg in self.__by_mat:
			if not isinstance(mg, ShapesGroup):
				raise Exception('GroupedShapes: Somehow non-ShapesGroup element appeared in groups by material: %s' % mg)
			shapes = mg()[1]
			while shapes:
				part, shapes = self.__extract_new_part(shapes)
				self.__parts.append(part)

	def __extract_new_part(self, shapes):
		"""
		Extracts a single part of objects which is under vertex limit
		:param shapes: list of CountedShape objects
		:return: tuple: (piece, left objects)
		"""
		if not isinstance(shapes, list):
			raise Exception('__extract_new_part: list expected as parameter')
		shapes = shapes[:]
		lim = self.max_vert
		cur_vert = 0
		all_checked = False
		part = list()
		while not all_checked:
			all_checked = True
			for i, s in enumerate(shapes):
				vert_sum = s.vertices(refresh=False) + cur_vert
				if vert_sum <= lim:
					all_checked = False
					part.append(shapes.pop(i))
					cur_vert = vert_sum
					break
		return part, shapes

	def __regroup(self):
		pending = self.unordered
		for sObj in pending:
			if not isinstance(sObj, CountedShape):
				raise Exception('GroupedShapes: Somehow non-CountedShape element appeared in unordered: %s' % sObj)
			shapePath = sObj.shape
			mats = ls.shapes_to_materials(shapePath)
			if len(mats) != 1:
				self.__errored.mat.add_shape(sObj)
			elif sObj.vertices(refresh=False) > self.max_vert:
				self.__errored.big.add_shape(sObj)
			else:
				self.__add_to_mat_group(mats[0], sObj)
			self.__unordered.remove_shape(sObj)
		self.__rebuild_from_matgroups()

	def mat_groups(self):
		return self.__by_mat

	@property
	def max_vert(self):
		return self.__max
	@max_vert.setter
	def max_vert(self, value):
		if not isinstance(value, int):
			raise Exception('GroupedShapes.max_vert: non-int value provided: %s' % value)
		self.__max = value
	@max_vert.deleter
	def max_vert(self):
		raise Exception('GroupedShapes.max_vert parameter cannot be deleted.')

	@property
	def unordered(self):
		return self.__unordered()[1]
	@unordered.setter
	def unordered(self, shapes):
		if not shapes is None:
			self.__unordered.add_shape(shapes)
			self.__regroup()
	@unordered.deleter
	def unordered(self):
		raise Exception('GroupedShapes.unordered parameter cannot be deleted.')

	@property
	def parts(self):
		return self.__parts[:]
	@parts.setter
	def parts(self, value):
		raise Exception('GroupedShapes.parts cannot be set directly.')
	@parts.deleter
	def parts(self):
		raise Exception('GroupedShapes.parts cannot be deleted.')

	@property
	def errors(self):
		return self.__errored
	@errors.setter
	def errors(self, value):
		raise Exception('GroupedShapes.errors cannot be set directly.')
	@errors.deleter
	def errors(self):
		raise Exception('GroupedShapes.errors cannot be deleted.')


# -----------------------------------------------------------------------------


class Splitter(object):
	__temp_gr = '|DRL_tmp_split'
	__temp_name_extender = '_DRL_tmp_name'
	def __init__(self, objects=None, limit=300, errorgroup_big='SPLIT_ERROR_too_big', errorgroup_mat='SPLIT_ERROR_materials'):
		self.__max = 300
		self.__src_objs = list()
		self.__errorgroup_name_big = ''
		self.__errorgroup_name_mat = ''
		self.__errored_big = list()
		self.__errored_mat = list()
		self.__current_source_matrix = list()
		self.result = list()
		self.max = limit
		self.errorgroup_big = errorgroup_big
		self.errorgroup_mat = errorgroup_mat
		self.src_objs = objects
		self.split_objects()

	def __perform_errored_processing(self, error_group, errGr_path, src_name, err_res):
		errored_shapes = [x.shape for x in error_group.items]
		for i, shp in enumerate(errored_shapes):
			path = mu.reparent_to_path(shp, errGr_path, **no_sel)[0]
			path = cmds.rename(path, '%s_err%d' % (src_name, i+1))
			path = hrc.to_full_paths(path, **no_sel)[0]
			tr.matrix_set(
				path, False,
				world_space=True,
				matrix=self.__current_source_matrix
			)
			err_res.append(path)

	def __perform_parts_generation(self, objects, src_name):
		res = list()
		shapes = hrc.to_children(objects, **no_sel)
		shapes = hrc.to_shapes(shapes, **no_sel)
		grouped = GroupedShapes(shapes, self.max)
		# errors - big:
		self.__perform_errored_processing(
			grouped.errors.big,
			self.errorgroup_big,
			src_name,
			self.__errored_big
		)
		# errors - mat:
		self.__perform_errored_processing(
			grouped.errors.mat,
			self.errorgroup_mat,
			src_name,
			self.__errored_mat
		)

		# correct groups:
		for idx, pt in enumerate(grouped.parts):
			nm = '%s_pt%d' % (src_name, idx+1)
			combined = [p.shape for p in pt]  # extract shape names first
			if len(combined) > 1:
				combined = cmds.polyUnite(combined, ch=False)[0]  # will return transform in world anyway
			else:
				combined = hrc.to_parents(combined, **no_sel)[0]  # get transform from shape
				combined = mu.reparent_to_world(combined, **no_sel)[0]
			combined = cmds.rename(combined, nm)
			res.append(combined)
		res_len = len(res)
		if res_len > 1:
			# multiple parts created
			res = cmds.group(res, world=True)
		elif res_len == 1:
			# single part created
			res = res[0]
		else:
			# no proper parts created, all of them are errored
			res = None
		return res

	def split_object(self, src_obj=None):
		src_obj = hrc.to_full_paths(src_obj, transforms=1)[0]
		self.__current_source_matrix = tr.matrix_get(src_obj, False, world_space=True)[0]
		res = cmds.duplicate(src_obj, returnRootsOnly=True)[0]
		res = mu.reparent_to_path(res, self.__temp_gr, **no_sel)[0]
		extra_children = hrc.to_child_non_shapes(res, selection_if_empty=False, type='mesh')
		if extra_children:
			cmds.delete(extra_children)
		del extra_children
		tr.reset(res, False, world_space=True)
		tr.reset_pivot(res, False)
		try:
			res = cmds.polySeparate(res, ch=False)
		except:
			pass
		res = hrc.to_full_paths(res, **no_sel)

		src_name = hrc.to_names(src_obj, **no_sel)[0]

		res = self.__perform_parts_generation(res, src_name)

		if cmds.ls(self.__temp_gr):
			cmds.delete(self.__temp_gr)
		if res is None:
			return res

		res = cmds.rename(res, src_name)
		res = hrc.to_full_paths(res, **no_sel)

		tr.matrix_set(
			res, False,
			world_space=True,
			matrix=self.__current_source_matrix
		)
		return res

	def split_objects(self):
		self.__errored_big = list()
		self.__errored_mat = list()
		self.result = list()
		len_objs = len(self.src_objs)
		for i, o in enumerate(self.src_objs):
			new_obj = self.split_object(o)
			if not new_obj is None:
				self.result += new_obj
			# print 'Finished: %s - %d of %d, %.2f' % (o, i+1, len_objs, (i+1.0)*100/len_objs) + '%'
		errored = self.__errored_big + self.__errored_mat
		if errored:
			cmds.select(errored, r=1)
		else:
			cmds.select(cl=1)

	@property
	def max(self):
		return self.__max
	@max.setter
	def max(self, value):
		if isinstance(value, float):
			value = int(value)
		elif not isinstance(value, int):
			raise Exception('Splitter.max can only take int value. Given: %s' % value)
		self.__max = value
	@max.deleter
	def max(self):
		raise Exception('Splitter.max cannot be deleted.')

	@property
	def src_objs(self):
		return self.__src_objs
	@src_objs.setter
	def src_objs(self, value):
		self.__src_objs = hrc.to_poly_hierarchy(value, selection_if_empty=True)
	@src_objs.deleter
	def src_objs(self):
		raise Exception('Splitter.src_objs cannot be deleted.')

	@property
	def errorgroup_big(self):
		return self.__errorgroup_name_big
	@errorgroup_big.setter
	def errorgroup_big(self, value):
		err.NotStringError(value, 'errorgroup_big').raise_if_needed()
		self.__errorgroup_name_big = value
	@errorgroup_big.deleter
	def errorgroup_big(self):
		Exception('Splitter.errorgroup_big cannot be deleted.')

	@property
	def errorgroup_mat(self):
		return self.__errorgroup_name_mat
	@errorgroup_mat.setter
	def errorgroup_mat(self, value):
		err.NotStringError(value, 'errorgroup_mat').raise_if_needed()
		self.__errorgroup_name_mat = value
	@errorgroup_mat.deleter
	def errorgroup_mat(self):
		Exception('Splitter.errorgroup_mat cannot be deleted.')