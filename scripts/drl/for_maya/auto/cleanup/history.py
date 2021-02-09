__author__ = 'Lex Darlog (DRL)'

import sys as __sys
from pymel import core as pm

from drl_common.py_2_3 import (
	str_t as _str_t,
	str_h as _str_h,
)

from drl.for_maya.ls import pymel as ls

from drl.for_maya import py_node_types as _pnt
_t_transform = _pnt.transform
_t_shape_any = _pnt.shape.any

_this = __sys.modules[__name__]


def __is_deformed(node):
	assert isinstance(node, (_t_transform, _t_shape_any))
	return any([
		isinstance(x, pm.nt.GeometryFilter)
		for x in node.listHistory(pruneDagObjects=1, groupLevels=1)
	])


def is_deformed(item=None, selection_if_none=True):
	"""
	Checks whether the given node is a deformed object.
		*
			If **None** or a Transform with no shapes is provided,
			the function always returns False.
		* If multiple items provided, only the 1st one is checked.
		* If Component provided, it's automatically handled as it's shape.

	:param item:
	:param selection_if_none:
	:return: <bool>
	"""
	item = ls.to_geo_nodes(item, selection_if_none, remove_duplicates=True)
	if not item:
		return False
	return __is_deformed(item[0])


def __to_nodes(items, selection_if_none):
	objects = set(ls.to_geo_nodes(items, selection_if_none))
	return set([
		x for x in objects if not x.intermediateObject.get()
	])


def __to_intermediates(objects_set):
	shapes_with_inters = set(
		ls.to_shapes(objects_set, False, geo_surface=True, include_intermediate=True)
	)
	shapes = set(ls.to_shapes(objects_set, False, geo_surface=True))
	return shapes_with_inters - shapes


def delete(items=None, selection_if_none=True):
	"""
	Delete entire history for the given items.

	Components are processed as shapes.
	Duplicates are removed before processing.

	:param items:
	:param selection_if_none:
	"""
	objects = __to_nodes(items, selection_if_none)
	if not objects:
		return _this
	pm.delete(objects, ch=True)
	inters = __to_intermediates(objects)
	if inters:
		pm.delete(inters)
	return _this


def __non_deformer_kwargs(before_deformers_only=False):
	"""
	Generate the list of keyword-arguments for bakePartialHistory command.
	Made accordingly to built-in doBakeNonDefHistory() MEL function.
	"""
	kw_args = dict()
	if before_deformers_only:
		kw_args['preDeformers'] = True
	else:
		kw_args['prePostDeformers'] = True
	post_smooth = pm.optionVar.get('bakeNonDefHistorySmooth')
	if not (post_smooth is None):
		kw_args['postSmooth'] = post_smooth
	return kw_args


def delete_non_deformer(items=None, selection_if_none=True, before_deformers_only=False):
	"""
	Delete non-deformer history on the given items.

	Components are processed as shapes.
	Duplicates are removed before processing.

	:param items:
	:param selection_if_none:
	:param before_deformers_only:
		<bool>

		Remove only the part of history that occur before the deformers.
			*
				When **False** (default), all the non-deformer modeling history is removed.
				No matter if it's before or after deformers.
	"""
	objects = __to_nodes(items, selection_if_none)
	if not objects:
		return _this

	kw_args = __non_deformer_kwargs(before_deformers_only)
	pm.bakePartialHistory(objects, **kw_args)
	return _this


def delete_all():
	"""
	Delete all the history in the entire scene.
	"""
	pm.delete(all=True, ch=True)
	all_objects = set(ls.all_objects())
	inters = __to_intermediates(all_objects)
	if inters:
		pm.delete(inters)
	return _this


def delete_all_non_deformer(before_deformers_only=False):
	"""
	Delete all non-deformer history in the entire scene.

	:param before_deformers_only:
		<bool>

		Remove only the part of history that occur before the deformers.
			* When **False** (default), all the non-deformer modeling history is removed.
	"""
	kw_args = __non_deformer_kwargs(before_deformers_only)
	pm.bakePartialHistory(all=True, **kw_args)
	return _this


def delete_smart(items=None, selection_if_none=True, before_deformers_only=False):
	"""
	For each provided object, automatically detect whether it's deformed and use
	either <Delete History> or <Delete non-Deformer History> on it respectively.

	:param items:
	:param selection_if_none:
	:param before_deformers_only:
		<bool>

		For deformed objects, tells to remove only the part of history
		that occur before the deformers.
			*
				When **False** (default), all the non-deformer modeling history is removed.
				No matter if it's before or after deformers.
	:return:
		<list of PyNodes>

		Transforms/Shapes which are deformed and therefore were cleaned-up
		with delete_non_deformer()
	"""
	objects = __to_nodes(items, selection_if_none)
	res = list()
	res_append = res.append
	for o in objects:
		if __is_deformed(o):
			delete_non_deformer(o, False, before_deformers_only)
			res_append(o)
		else:
			delete(o, False)
	return res