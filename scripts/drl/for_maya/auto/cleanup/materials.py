__author__ = 'DRL'

import sys as __sys
from pymel import core as _pm

from drl_common.py_2_3 import (
	str_t as _str_t,
	str_h as _str_h,
)

from drl.for_maya.ls import pymel as _ls

from drl.for_maya import py_node_types as _pnt
_t_shape_poly = _pnt.shape.poly
_t_shape_nurbs = _pnt.shape.nurbs

_pm_ls = _pm.ls
_ls_sorted = _ls.sorted_items
_mat = _ls.materials

_this = __sys.modules[__name__]


def all_faces_to_shape(items=None, selection_if_none=True):
	"""
	Reassign material to the shape itself, if it's assigned to all of the faces.
	Currently only polygonal and NURBS faces are supported.

	:return: <list of PyNodes> Shapes that was cleaned-up.
	"""
	shapes = _mat.items_to_shapes(items, selection_if_none)

	res = list()
	res_append = res.append

	to_comps_mesh = lambda s: s.faces
	to_comps_nurbs = lambda s: s.sf

	def _check_known_shape(sg, shape, components, to_comps_f):
		sorted_assigned = _ls_sorted(
			_pm_ls(components, fl=1),
			False
		)
		if sorted_assigned != _ls_sorted(
			_pm_ls(to_comps_f(shape), fl=1),
			False
		):
			return
		_pm.sets(sg, remove=components)
		_pm.sets(sg, forceElement=shape)
		res_append(shape)

	def _check_mesh(sg, shape, components):
		_check_known_shape(sg, shape, components, to_comps_mesh)

	def _check_nurbs(sg, shape, components):
		_check_known_shape(sg, shape, components, to_comps_nurbs)

	def _check_shape(shape):
		grouped = _mat.AssignedTo(shape, False).grouped_by_sg()
		if len(grouped) != 2 or grouped[-1][1]:
			return

		# now we know a single SG connected to the shape ...

		sg, s_items = grouped[0]
		if not s_items:
			return
		# ... and group is not empty

		if isinstance(shape, _t_shape_poly):
			return _check_mesh(sg, shape, s_items)

		if isinstance(shape, _t_shape_nurbs):
			return _check_nurbs(sg, shape, s_items)

	map(_check_shape, shapes)

	return res