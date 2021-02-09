__author__ = 'DRL'

import re as _re
from functools import partial as _partial

from pymel import core as pm

from drl_common.py_2_3 import (
	str_t as _str_t,
	str_h as _str_h,
)

default_regex = r'^.+_{}[_\d]*$'


def __find_targets_for_single_source(src, match_regex=default_regex):
	"""
	Find all the target objects for the given source
	and the specified regex pattern.

	:param src: <PyNode> Source object, transform.
	:param match_regex:
		<str>

		Regex pattern. I.e., a string that will become regex
		after performing .format(src_nm) on it.
	:return: <list of PyNodes> target objects, transforms.
	"""
	from drl.for_maya.ls import pymel as ls

	src_nm = ls.short_item_name(src)
	regex_compiled = _re.compile(match_regex.format(src_nm))
	return [
		t for t in pm.ls('*{}*'.format(src_nm), tr=1)
		if (
			t != src and
			regex_compiled.match(ls.short_item_name(t))
		)
	]


def __replace_shapes_with_object(
	src_object, targets, pre_update_f=None, geo_shape_only=True
):
	"""
		Replace all the shapes and children with the ones from a given single object.

		:param src_object: Source object, transform.
		:type src_object: pm.PyNode
		:param targets: Objects to replace their shapes/children.
		:type targets: list[pm.nt.Transform]
		:param pre_update_f:
			Optional function that's called before removing current target's children
			and adding instances.

			It takes the current target and returns it, too (in case it was modified).
			If it wasn't modified, just pass it through.
		:type pre_update_f: (pm.nt.PyNode | pm.nt.Transform) -> (pm.nt.PyNode | pm.nt.Transform)
		:param geo_shape_only: Whether to look only for a geo-shape of the source object.
		:type geo_shape_only: bool
		:return:
			List of newly instanced shapes and children.
				* immediate shapes are instances.
				*
					immediate children are created the same way Maya's "instantiate" works.
					i.e., the created child's transform is is a "full" object,
					while all of it's own children (both transforms and shapes) are instances.
		:rtype: list[pm.PyNode]
	"""
	from drl.for_maya import geo
	from drl.for_maya.ls import pymel as ls

	src_shape = ls.to_shapes(src_object, False, geo_surface=geo_shape_only)[0]
	children = pm.listRelatives(src_object, children=1, type='transform')
	res = list()
	res_append = res.append

	targets = geo.instance_to_object(targets, False)

	def _process_single_target_only(target):
		# remove anything under target transform:
		old_children = pm.listRelatives(target, children=1)
		pm.delete(old_children)

		instanced_shape = pm.parent(src_shape, target, shape=1, relative=1, addObject=1)
		res_append(instanced_shape)
		for c in children:
			dup = pm.instance(c, leaf=1)[0]
			dup = pm.parent(dup, target, relative=1)[0]
			dup = pm.rename(dup, ls.short_item_name(c))
			res_append(dup)

	def _process_single_target_with_f(target):
		target = pre_update_f(target)
		_process_single_target_only(target)

	if pre_update_f is None:
		map(_process_single_target_only, targets)
	else:
		map(_process_single_target_with_f, targets)
	return res


def from_many_sources(match_regex=None):
	"""
	Select source trees (transforms) first, their shapes will replace
	all the other trees in the scene, if they're named correspondingly.

	:param match_regex:
		Optional regular expression that determines the rule to match
		new object's name with the old one.

		If none provided, default is used.
	:return:
		<list of PyNodes>

		List of newly instanced shapes and children.
			* immediate shapes are instances.
			*
				immediate children are created the same way Maya's "instantiate" works.
				i.e., the created child's transform is is a "full" object,
				while all of it's own children (both transforms and shapes) are instances.
	"""
	src_objects = pm.ls(sl=1, tr=1)
	# src = src_objects[0]

	if match_regex is None or not isinstance(match_regex, _str_t):
		match_regex = default_regex

	res = list()
	res_extend = res.extend

	_get_targets = _partial(
		__find_targets_for_single_source,
		match_regex=match_regex
	)

	def _transfer_single_source(src_obj):
		targets = _get_targets(src_obj)
		res_extend(
			__replace_shapes_with_object(src_obj, targets)
		)

	map(_transfer_single_source, src_objects)

	pm.select(res, r=1)
	return res


def from_many_sources_with_offset(match_regex=None):
	"""
	Designed to replace the current trees (made of old shapes with old pivot) with the new ones.
	I.e., this function updates not only a mesh, but also it's transform.

	Select source trees (transforms) first, their shapes will replace
	all the other trees in the scene, if they're named correspondingly.

	Each tree has to be parented to a transform representing the old tree mesh. I.e.:
	* parent - old tree geo, with old pivot/transform
	* child - new tree geo (shape is changed/offset relatively to pivot/transform)

	Parent and child need to look the same (but, obviously, child's transform is offset)

	:param match_regex:
		Optional regular expression that determines the rule to match
		new object's name with the old one.

		If none provided, default is used.
	:return:
		<list of PyNodes>

		List of newly instanced shapes and children.
			* immediate shapes are instances.
			*
				immediate children are created the same way Maya's "instantiate" works.
				i.e., the created child's transform is is a "full" object,
				while all of it's own children (both transforms and shapes) are instances.
	"""
	src_objects = pm.ls(sl=1, tr=1)
	# src = src_objects[0]

	if match_regex is None or not isinstance(match_regex, _str_t):
		match_regex = default_regex

	res = list()
	res_extend = res.extend

	_get_targets = _partial(
		__find_targets_for_single_source,
		match_regex=match_regex
	)

	def _transfer_single_source(src_obj):
		local_xform = pm.xform(src_obj, q=1, relative=1, objectSpace=1, matrix=1)

		def _fix_xform_of_single_target(target):
			tmp_dup = pm.duplicate(src_obj)[0]
			tmp_dup = pm.parent(tmp_dup, target, relative=1)[0]
			pm.xform(tmp_dup, absolute=1, objectSpace=1, matrix=local_xform)
			ws_xform = pm.xform(tmp_dup, q=1, absolute=1, worldSpace=1, matrix=1)
			pm.xform(target, absolute=1, worldSpace=1, matrix=ws_xform)
			return target

		targets = _get_targets(src_obj)
		res_extend(
			__replace_shapes_with_object(
				src_obj, targets,
				pre_update_f=_fix_xform_of_single_target
			)
		)

	map(_transfer_single_source, src_objects)

	pm.select(res, r=1)
	return res


def source_to_targets(
	targets=None, source=None, selection_if_none=True, geo_shape_only=False
):
	"""
	Replace given targets' shapes and children with the ones from given source.

	The arguments fallback sequence is:
		* both targets and source are specified.
		* only targets specified -> the last item is considered as source
		*
			targets are None, and <selection_if_none> is true ->
			selection is used, last item is source.
		* nothing processed, empty list returned.

	:param targets: Target objects (transforms).
	:type targets: list[None | string | pm.PyNode]
	:param source: Source object
	:type source: None | string | pm.PyNode
	:param geo_shape_only: Whether to look only for a geo-shape of the source object.
	:type geo_shape_only: bool
	:return:
		List of newly instanced shapes and children.
			* immediate shapes are instances.
			*
				immediate children are created the same way Maya's "instantiate" works.
				i.e., the created child's transform is is a "full" object,
				while all of it's own children (both transforms and shapes) are instances.
	:rtype: list[pm.PyNode]
	"""
	from drl.for_maya.ls.pymel import default_input
	targets = default_input.handle_input(targets, selection_if_none)
	if not targets:
		return list()

	source = default_input.handle_input(source, False)
	if source:
		source = source[0]
	else:
		source = targets.pop()
		if not targets:
			return list()

	return __replace_shapes_with_object(source, targets, geo_shape_only=geo_shape_only)