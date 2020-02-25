__author__ = 'DRL'

from pymel import core as pm
from drl.for_maya.ls import pymel as ls
from drl_common import errors as err
from drl_common import utils
from drl_common.py_2_3 import (
	str_t as _str_t,
	str_hint as _str_h,
	typing as _t
)

from drl.for_maya import py_node_types as _pnt
_t_transform = _pnt.transform
_t_shape_any = _pnt.shape.any
_t_shape_poly = _pnt.shape.poly


class MultipleShapesError(RuntimeError):
	def __init__(self, obj=None, formatted_message=None):
		super(MultipleShapesError, self).__init__()
		if not(
			formatted_message and isinstance(formatted_message, _str_t)
		):
			formatted_message = 'Object has multiple shapes: {obj}'
		message = formatted_message.format(obj=obj)
		super(MultipleShapesError, self).__init__(message)
		self.obj = obj


class UVSetError(RuntimeError):
	def __init__(self, obj, uv_set, formatted_message=None):
		if not formatted_message or not isinstance(formatted_message, _str_t):
			formatted_message = 'Error while performing operation with uv-set <{uv_set}> on object: {obj}'
		message = formatted_message.format(uv_set=uv_set, obj=obj)
		super(UVSetError, self).__init__(message)
		self.obj = obj
		self.uv_set = uv_set


class UVSetCopyToItselfError(UVSetError):
	def __init__(self, obj, uv_set):
		super(UVSetCopyToItselfError, self).__init__(
			obj, uv_set,
			"Can't copy UV-set <{uv_set}> to itself for the object: {obj}"
		)


class NoSuchUVSetError(UVSetError):
	def __init__(self, obj, uv_set, formatted_message=None):
		if not formatted_message or not isinstance(formatted_message, _str_t):
			formatted_message = "UV-set <{uv_set}> not found in the object: {obj}"
		super(NoSuchUVSetError, self).__init__(
			obj, uv_set,
			formatted_message
		)


class NoSuchUVSetIndexError(NoSuchUVSetError):
	def __init__(self, obj, uv_set_number, formatted_message=None):
		if not formatted_message or not isinstance(formatted_message, _str_t):
			formatted_message = "Object {obj} doesn't have {uv_set} UV-sets."
		super(NoSuchUVSetIndexError, self).__init__(
			obj, uv_set_number,
			formatted_message
		)


def __error_check_object(obj):
	obj = ls.default_input.handle_input(obj, selection_if_none=False)
	if not obj:
		raise ValueError("No such object: %s" % obj)
	obj = obj[0]
	err.WrongTypeError(obj, (_t_transform, _t_shape_poly), 'item', 'mesh object').raise_if_needed()
	return obj


def __error_check_object_and_set(obj, uv_set, all_sets=None):
	"""
	Makes sure the given object is a single transform/mesh node;
	converts the provided set to it's name.

	:param obj: The scene object to get UV-set for.
	:param uv_set: either a name or a number of a UV-set.
	:param all_sets: pre-gathered list of UV-set names, kinda cache optimization.
	:return: (nt.Transform or nt.Mesh, string) object and set name
	"""
	obj = __error_check_object(obj)

	if not all_sets:
		all_sets = get_object_sets(obj)

	if isinstance(uv_set, int):
		if uv_set > len(all_sets):
			raise NoSuchUVSetIndexError(obj, uv_set)
		uv_set = all_sets[uv_set - 1]
		err.WrongTypeError(uv_set, _str_t, 'all_sets', 'string').raise_if_needed()
	elif isinstance(uv_set, _str_t):
		if not uv_set in all_sets:
			raise NoSuchUVSetError(obj, uv_set)
	else:
		raise TypeError(
			'Either int or string expected for <uv_set> argument. Got: ' + repr(uv_set)
		)
	assert isinstance(uv_set, _str_t)
	return obj, uv_set


def get_object_sets(obj):
	"""Legacy only. Use `get_sets()` instead."""
	obj = __error_check_object(obj)
	return pm.polyUVSet(obj, q=1, allUVSets=1)


def get_sets(item, selection_if_none=False):
	"""List all UV-sets present on the given object."""
	shapes = ls.to_shapes(item, selection_if_none, geo_surface=True)
	res = list()  # type: _t.List[_str_h]
	if not shapes:
		return res
	if len(shapes) != 1:
		raise MultipleShapesError(item)
	res = pm.polyUVSet(shapes[0], q=1, allUVSets=1)
	return res


def get_current(obj):
	"""
	Returns the currently active UV set for the specified object.

	:param obj: Transform or Mesh node
	:return: (string) the name of the active UV set
	"""
	obj = __error_check_object(obj)
	uv_set = pm.polyUVSet(obj, q=1, currentUVSet=1)[0]
	assert isinstance(uv_set, _str_t)
	return uv_set


def set_current_for_singe_obj(obj, uv_set, all_sets=None):
	"""
	Sets the currently active UV set for the specified object.

	:param obj: Transform or Mesh node
	:param uv_set: (int / string) The number or the name for the set
	:param all_sets: pre-gathered list of UV-set names, kinda cache optimization.
	:return: <Transform/Mesh> if UV-set was changed, <None> if this set is already active.
	"""
	obj, uv_set = __error_check_object_and_set(obj, uv_set, all_sets)
	if uv_set == get_current(obj):
		return None
	pm.polyUVSet(obj, currentUVSet=1, uvSet=uv_set)
	return obj


def set_current(items=None, uv_set=None, selection_if_none=True):
	"""
	Sets the currently active UV set for an arbitrary given input.
	I.e., shapes detected automatically, multiple items can be given at once.
	Even components can be given.

	The function is error-safe, i.e.:
		* if None/0 is given as the <uv_set>, or...
		* if no items given, ...
	Then nothing is performed and empty list is returned with no error.

	:param items: <list> Source elements (objects/components) of a scene to be converted.
	:param uv_set:
		<int / string>

		The number or the name for the set:
			* None/0 - current (don't change)
			* <str> - name
			* <int> - 1-based UV-set number
	:param selection_if_none: <bool> whether to use current selection if items is None.
	:return: list of <Mesh> shapes for which UV-set has been changed.
	"""
	if (
		uv_set is None or
		(isinstance(uv_set, int) and uv_set == 0) or
		not items
	):
		return []

	shapes = set(ls.to_shapes(items, selection_if_none, geo_surface=True))
	if not shapes:
		return []

	res = list()
	for s in shapes:
		changed = set_current_for_singe_obj(s, uv_set)
		if changed:
			res.append(changed)
	return res


def get_set_name(obj, uv_set=None, all_sets=None):
	"""
	If uv-set not provided, returns current uv-set.
	If provided, returns uv-set name and throws an error if it doesn't exist.

	:param obj: The scene object to get UV-set for.
	:param uv_set: either a name or a number (starting at 1) of a UV-set, None or 0 to get current set.
	:param all_sets: pre-gathered list of UV-set names, kinda cache optimization.
	:return:
	"""
	if not uv_set:
		return get_current(obj)

	return __error_check_object_and_set(obj, uv_set, all_sets)[1]


def copy_to_set(objects=None, to_set=1, from_set='', selection_if_none=True, **kwargs):
	"""
	Copies one set to another. Handles multiple-objects copying and uv-set numer instead of name.
	:param objects: objects in scene to process
	:param to_set: UV-set name or number (starting with 1) to copy UVs to
	:param from_set: source UV-set name or number
	:param selection_if_none: whether to use selection when no objects given
	:param kwargs: extra arguments passed to polyCopyUV command
	"""
	objects = ls.default_input.handle_input(objects, selection_if_none=selection_if_none)
	if not to_set:
		to_set = 1

	def copy_single(obj):
		all_sets = get_object_sets(obj)
		current = get_current(obj)
		to_name = get_set_name(obj, to_set, all_sets=all_sets)
		from_name = get_set_name(obj, from_set, all_sets=all_sets)
		if current != from_name:
			pm.polyUVSet(obj, currentUVSet=1, uvSet=from_name)
		if from_name == to_name:
			raise UVSetCopyToItselfError(obj, uv_set=from_name)
		pm.polyCopyUV(obj, uvSetNameInput=from_name, uvSetName=to_name, **kwargs)

	res = []
	errors = []
	for o in objects:
		try:
			copy_single(o)
			res.append(o)
		except UVSetCopyToItselfError:
			errors.append(o)
	if errors:
		print (
			'Unable to copy sets for following objects:\n\t'
			+ '\n\t'.join([repr(x) for x in errors])
		)
	pm.select(res, r=1)


def remove(objects=None, uv_sets=None, selection_if_none=True):
	"""
	Removes the provided UV-sets for the given objects.

	If some of the given objects doesn't contain a given UV-sets, it's just skipped (no error thrown).

	:param objects: objects in scene to process
	:param uv_sets:
		<int/string or list of them>
			* either a name or a number (starting at 1) of a UV-set,
			* None or 0 to get current set.
	:param selection_if_none: whether to use selection when no objects given
	:return:
		list of 2-value tuples, describing which sets was removed:
			* <PyNode> shape containing sets
			* <tuple of strings> UV-set names
	"""
	if not uv_sets:
		return []
	if isinstance(uv_sets, float):
		uv_sets = int(uv_sets)
	if isinstance(uv_sets, (int, str, unicode)):
		uv_sets = (uv_sets,)
	if isinstance(uv_sets, list):
		uv_sets = tuple(uv_sets)
	uv_sets = err.WrongTypeError(uv_sets, tuple, 'uv_sets').raise_if_needed()

	objects = ls.to_objects(
		objects, selection_if_none,
		shape_to_object=False, component_to_shape=True, remove_duplicates=True
	)
	shapes = list()
	for o in objects:
		if isinstance(o, _t_shape_any):
			shapes.append(o)
			continue
		shapes.extend(
			ls.to_shapes(o, False, geo_surface=True)
		)
	if not shapes:
		return []
	shapes = utils.remove_duplicates(shapes)
	res = list()

	def _del_for_shape(shape):
		set_nm = ''
		removed_sets = list()
		for u in uv_sets:
			skip = False
			try:
				set_nm = get_set_name(s, u)
			except NoSuchUVSetError:
				skip = True
			if skip:
				continue
			removed_sets.append(set_nm)
		if not removed_sets:
			return
		removed_sets = tuple(sorted(list(set(removed_sets))))
		for r in removed_sets:
			pm.polyUVSet(o, delete=1, uvSet=r)
		res.append((shape, removed_sets))

	for s in shapes:
		_del_for_shape(s)

	return res


def rename(items=None, uv_set=1, new_name='map1', selection_if_none=True):
	"""
	Error-safe UV'-sets rename for a bunch of objects

	:param items: objects/components in scene to process
	:param uv_set: <int/string> UV-set to rename.
	:param new_name: <string>
	:param selection_if_none: whether to use selection when no items are given
	:return: <list of PyNodes> renamed sets' shapes.
	"""
	if isinstance(uv_set, float):
		uv_set = int(uv_set)
	uv_set = err.WrongTypeError(uv_set, (int, str, unicode), 'uv_set').raise_if_needed()
	new_name = err.NotStringError(new_name, new_name).raise_if_needed_or_empty()
	shapes = ls.to_shapes(items, selection_if_none, geo_surface=True)
	res = list()
	for s in shapes:
		skip = False
		try:
			src_set = get_set_name(s, uv_set)
		except NoSuchUVSetError:
			skip = True
		if skip or src_set == new_name:
			continue
		pm.polyUVSet(s, rename=1, uvSet=src_set, newUVSet=new_name)
		res.append(s)
	return res


def keep_only_main_set(objects=None, fix_default_set_name=True, selection_if_none=True, **kwargs):
	"""
	Cleans up all extra UV-sets on the given objects.

	:param objects: objects in scene to process
	:param selection_if_none: whether to use selection when no objects given
	:param fix_default_set_name: when True, the names of the kept set will be forced to 'map1'
	:param kwargs: extra arguments passed to polyUVSet command
	"""
	kept_set = 1
	objects = ls.default_input.handle_input(objects, selection_if_none=selection_if_none)

	def keep_single(obj):
		all_sets = get_object_sets(obj)
		current = get_set_name(obj, all_sets=all_sets)
		main_set = get_set_name(obj, kept_set, all_sets=all_sets)
		if current != main_set:
			pm.polyUVSet(obj, currentUVSet=1, uvSet=main_set)
			# current = main_set
		for s in all_sets[kept_set:]:
			pm.polyUVSet(obj, delete=1, uvSet=s, **kwargs)
		if fix_default_set_name and main_set != 'map1':
			pm.polyUVSet(obj, rename=1, uvSet=main_set, newUVSet='map1')

	for o in objects:
		keep_single(o)
	pm.select(objects, r=1)


def filter_by_set(
		items=None, selection_if_none=True, uv_set='map1', exclude=False
):
	"""Filter objects by either having or not a UV-set with a specific name."""
	if not(uv_set and isinstance(uv_set, _str_t)):
		return items

	items = ls.to_objects(
		items, selection_if_none, shape_to_object=False, component_to_shape=True,
		remove_duplicates=True
	)

	def has_set(set_name, uv_sets):
		return set_name in uv_sets

	def doesnt_have_set(set_name, uv_sets):
		return set_name not in uv_sets

	is_kept = doesnt_have_set if exclude else has_set

	def gen_kept(
		objects  # type: _t.List[pm.PyNode]
	):
		for obj in objects:
			try:
				sets = get_sets(obj, False)
				if is_kept(uv_set, sets):
					yield obj
			except MultipleShapesError:
				shapes = ls.to_shapes(obj, False, geo_surface=True)
				for shape in shapes:
					sets = get_sets(obj, False)
					if is_kept(uv_set, sets):
						yield shape

	return list(gen_kept(items))
