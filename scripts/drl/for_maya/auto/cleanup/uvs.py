__author__ = 'DRL'

from itertools import izip as _izip
from functools import partial as _part
from collections import deque as _deque

import pymel.core as _pm

from drl_common.utils import group_items as _group_items

from drl.for_maya.ls.convert.components import Poly as _PolyConvert, vfs_grouped_by_vertex

from drl.for_maya import py_node_types as _pnt

_t_uv = _pnt.comp.poly.uv

import math as _math

_sqrt_2 = _math.sqrt(2.0)


def _do_uvs_match_raw(uv_1, uv_2, allowed_delta=0.00048828125):
	u1, v1, u2, v2 = _pm.polyEditUV((uv_1, uv_2), q=1)
	return (
		abs(u1 - u2) <= allowed_delta and
		abs(v1 - v2) <= allowed_delta
	)


def do_uvs_match(uv_1, uv_2, resolution=1024, pixel_fraction=0.5):
	"""
	Checks whether two given UVs are located at approximately the same position.

	:param uv_1: <pm.MeshUV>
	:param uv_2: <pm.MeshUV>
	:param resolution:
		<int / float>

		Which resolution to check for.
	:param pixel_fraction:
		<float>

		The (Manhattan-style) distance between UVs needs to be less then or equal to
		this part of a pixel size.
	:return: <bool> are UVs close enough to consider as snapped?
	"""
	return _do_uvs_match_raw(uv_1, uv_2, float(pixel_fraction) / resolution)


__edge_to_vf_non_flat = _part(
	_pm.polyListComponentConversion, fromEdge=True, toVertexFace=True
)
__vf_to_uv_non_flat = _part(
	_pm.polyListComponentConversion, fromVertexFace=True, toUV=True
)
_flatten = _part(_pm.ls, fl=1)
_edge_to_vf = lambda e: _flatten(__edge_to_vf_non_flat(e))
_vf_to_uv = lambda u: _flatten(__vf_to_uv_non_flat(u))


class UVs(_PolyConvert):

	def sew_extra_seams(self, resolution=1024, pixel_fraction=0.5):
		uvs = self.to_uvs(flatten=False)
		if not uvs:
			return self

		prev_sl = _pm.ls(sl=1)
		prev_hl = _pm.ls(hl=1)

		uvs_per_shape = _group_items(uvs, key_f=lambda x: x.node().name())  # list of tuples

		allowed_delta = float(pixel_fraction) * _sqrt_2 * 1.001 / resolution
		process_single_shape_uvs = _part(
			_pm.polyMergeUV,
			ch=False, worldSpace=False, distance=allowed_delta
		)
		map(process_single_shape_uvs, uvs_per_shape)

		try:
			_pm.select(prev_sl, r=1)
		except:
			pass

		try:
			_pm.hilite(prev_hl, r=1)
		except:
			pass

		return self


		#
		# def are_uvs_close(pos_a, pos_b):
		# 	# pos_a = (u1, v1)
		# 	# pos_b = (u2, v2)
		# 	return all(map(
		# 		lambda a, b: abs(a - b) <= allowed_delta,
		# 		*_izip(pos_a, pos_b)
		# 	))
		#
		# def is_edge_end_snapped(vertex_faces_tuple):
		# 	uvs = _vf_to_uv(vertex_faces_tuple)
		# 	assert isinstance(uvs, list)
		# 	num_uvs = len(uvs)
		# 	if num_uvs < 2:
		# 		return True
		#
		# 	uvs = _pm.polyEditUV(uvs, q=1)  # [u1, v1, u2, v2...]
		# 	uvs = _deque(
		# 		_izip(*[iter(uvs)] * 2),  # [(u1, v1), (u2, v2)...]
		# 		num_uvs
		# 	)
		# 	uv0 = uvs.popleft()
		# 	is_cur_uv_close = _part(are_uvs_close, uv0)
		#
		# 	return all(map(is_cur_uv_close, uvs))
		#
		# to_sew = list()
		# to_sew_append = to_sew.append
		#
		# def add_edge_to_list_if_snapped(edge):
		# 	vertex_faces = _edge_to_vf(edge)  # for now, it's flat list
		# 	if len(vertex_faces) < 3:
		# 		# it's a border edge
		# 		return
		#
		# 	vertex_faces = vfs_grouped_by_vertex(vertex_faces, single_shape=True)  # [ (,) ]
		# 	if all(map(is_edge_end_snapped, vertex_faces)):
		# 		to_sew_append(edge)
		#
		# map(add_edge_to_list_if_snapped, seam_edges)