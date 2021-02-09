__author__ = 'Lex Darlog (DRL)'

from pymel import core as pm
from drl_common.py_2_3 import (
	str_t as _str_t,
	str_h as _str_h,
)
from drl.for_maya.ls import pymel as ls

_mesh_type = pm.nt.Mesh


def _to_shapes(items=None, selection_if_none=True):
	return ls.to_shapes(items, selection_if_none, exact_type=_mesh_type)


def _ensure_mesh(node):
	assert isinstance(node, _mesh_type)
	return node


def _get_all_sets(shape):
	res = shape.getColorSetNames()
	assert isinstance(res, list)
	return res


def get_all_sets(obj=None, selection_if_none=True):
	obj = _to_shapes(obj, selection_if_none)
	if not obj:
		return []
	return _get_all_sets(obj[0])


def get_current(obj=None, selection_if_none=True):
	obj = _to_shapes(obj, selection_if_none)
	if not obj:
		return ""
	res = obj[0].getCurrentColorSetName()
	assert isinstance(res, _str_t)
	return res


def delete_all_sets(items=None, selection_if_none=True):
	"""
	Removes all the Color-sets for the given objects.

	:param items: nodes/components.
	:param selection_if_none: whether to use selection if <items> is None
	:return: <list of PyNodes> shapes which color-sets was removed.
	"""
	shapes = _to_shapes(items, selection_if_none)

	res = list()

	def _delete_for_single(shape):
		all_sets = _get_all_sets(shape)
		if not all_sets:
			return
		for st in all_sets:
			shape.deleteColorSet(st)
		res.append(shape)

	for s in shapes:
		_delete_for_single(s)
	return res


def shapes_with_color_sets(items=None, selection_if_none=True):
	shapes = _to_shapes(items, selection_if_none)
	return [s for s in shapes if _get_all_sets(s)]


def shapes_with_no_color_sets(items=None, selection_if_none=True):
	shapes = _to_shapes(items, selection_if_none)
	return [s for s in shapes if not _get_all_sets(s)]