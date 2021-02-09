__author__ = 'DRL'

import re

from pymel import core as _pm
from drl_common.py_2_3 import (
	str_t as _str_t,
	str_h as _str_h,
)
from drl.for_maya.ls import pymel as _ls
from drl.for_maya.ls.convert import components as _conv_comp
from drl.for_maya.auto.cleanup import history as _h
from .. import freeze_transform as _freeze
from drl.for_maya.transformations import reset_pivot as _reset

try:
	# support type hints:
	import typing as _t
	_h_node = _t.Union[_str_h, _pm.PyNode]
	_t_face = _pm.general.MeshFace
except ImportError:
	pass


def group_by_shape(
	items=None,  # type: _t.Union[None, _h_node, _t.Iterable[_h_node]]
	selection_if_none=True
):
	"""
	Take a flat list of poly faces/objects,
	convert it to a list of lists, containing faces grouped by their shape.

	Internally, all the objects are converted to faces first.
	"""
	default_res = list(list())  # type: _t.List[_t.List[_t_face]]
	items = _ls.default_input.handle_input(items, selection_if_none, flatten=False)
	if not items:
		return default_res
	items = _conv_comp.Poly(items, selection_if_none=False).to_faces()  # type: _t.List[_t_face]
	if not items:
		return default_res

	items_sorted = dict()  # type: _t.Dict[str, _t.Tuple[int, _t.List[_t_face]]]
	# store as dict, where:
	# key is a shape's full name
	# value is a tuple:
	# * sort order of the group (reauired to later restore the original order of shapes)
	# * the actual list of shape's faces
	for i, itm in enumerate(items):
		shape_nm = _ls.long_item_name(itm, keep_comp=False)
		try:
			cur_tuple = items_sorted[shape_nm]
		except KeyError:
			cur_list = list()  # type: _t.List[_t_face]
			cur_tuple = (i, cur_list)
			items_sorted[shape_nm] = cur_tuple
		cur_tuple[1].append(itm)

	items_sorted = sorted(
		items_sorted.values(),
		key=lambda x: x[0]
	)  # type: _t.List[_t.Tuple[int, _t.List[_t_face]]]
	items_sorted = [tpl[1] for tpl in items_sorted]  # type: _t.List[_t.List[_t_face]]
	return items_sorted


def separate(
	items=None,  # type: _t.Union[None, _h_node, _t.Iterable[_h_node]]
	selection_if_none=True,
	combine_parts=False
):
	"""
	More user-friendly poly-separate.

	Unlike default Maya's "Separate" function, this one:
		* gives more friendly names to the newly created pieces
		* cleans up the extra transforms after separation
		* optionally combines separated parts into a single object.

	:param combine_parts:
		when `True`, the selected pieces are separated as a single object.
	:return:
		Only the extracted pieces (not the main one). They are also selected.
	"""
	faces_grouped = group_by_shape(items, selection_if_none)
	res = list()  # type: _t.List[_t.Union[_pm.nodetypes.Transform, _pm.PyNode]]
	if not faces_grouped:
		return res

	def keep_transforms(src_objects):
		return [
			o for o in src_objects
			if isinstance(o, _pm.nodetypes.Transform)  # exclude the history object
		]

	re_part_name = re.compile('(.*)_pt\d+$')

	for shape_faces in faces_grouped:
		if not shape_faces:
			continue

		# iteratively process all the selected shapes:
		shape = shape_faces[0].node()
		orig_transform = shape.parent(0)
		orig_name = orig_transform.nodeName()  # type: _str_h
		orig_was_part = bool(  # original mesh's name already ends with "_pt#"
			re_part_name.match(orig_name.lower())
		)
		orig_parent = orig_transform.firstParent2()  # type: _t.Optional[_pm.nodetypes.Transform]

		# detect shell IDs to separate:
		_pm.select(shape_faces, r=1)
		selected_shells = _pm.polyEvaluate(activeShells=1)  # type: _t.List[long]
		sep_objects = keep_transforms(  # exclude the history object
			_pm.polySeparate(shape, sss=selected_shells)
		)
		sep_main = sep_objects.pop()

		if combine_parts and sep_objects:
			_h.delete_smart(sep_objects, selection_if_none=False)
			sep_objects = keep_transforms(
				_pm.polyUnite(sep_objects, mergeUVSets=1)
			)
			if sep_objects:
				# temporary parent to a main part, to fix transform
				_pm.parent(sep_objects, sep_main)
				_freeze(sep_objects, selection_if_none=False)
				_reset(sep_objects, selection_if_none=False)

		# sequentially unparent, to make the main part first:
		if orig_parent:
			_pm.parent(sep_main, orig_parent)
			_pm.parent(sep_objects, orig_parent)
		else:
			_pm.parent(sep_main, w=1)
			_pm.parent(sep_objects, w=1)
		_h.delete_smart(sep_objects + [sep_main], selection_if_none=False)

		_pm.rename(sep_main, orig_name)
		orig_name = sep_main.name()  # type: _str_h
		if orig_was_part:
			pt_name = orig_name
		else:
			pt_name = orig_name + '_pt1'

		for pt in sep_objects:
			_pm.rename(pt, pt_name)
		res.extend(sep_objects)

	_pm.select(res, r=1)
	return res
