__author__ = 'DRL'

from pymel import core as pm
from drl.for_maya.ls import pymel as ls
from drl_common import errors as err
from drl.for_maya.ls.convert import components as comp
from drl.for_maya import ui

from . import uv_sets


def _perform_with_mesh_uvs(
	objs=None, uv_set=None, selection_if_none=True,
	modify_u_f=None, modify_v_f=None,
	do_u_f=None, do_v_f=None,
	**kwargs
):
	"""
	Common function for performing some UV modifications for the given mesh objects (not uv components).
	"""
	meshes = [
		x for x in ls.to_shapes(objs, selection_if_none)
		if isinstance(x, pm.nodetypes.Mesh)
	]
	do_u = do_u_f(**kwargs) if not do_u_f is None else True
	do_v = do_v_f(**kwargs) if not do_v_f is None else True

	if not do_u:
		print('U is not changed.')
	if not do_v:
		print('V is not changed.')

	if not meshes or not (do_u or do_v):
		return []

	for m in meshes:
		assert isinstance(m, pm.nodetypes.Mesh)
		cur_set = (
			uv_set if uv_set and isinstance(uv_set, (str, unicode))
			else m.getCurrentUVSetName()
		)
		new_u, new_v = m.getUVs(cur_set)

		if do_u:
			new_u = [modify_u_f(src, **kwargs) for src in new_u]
		if do_v:
			new_v = [modify_v_f(src, **kwargs) for src in new_v]

		m.setUVs(new_u, new_v, cur_set)

	return meshes


def gamma_uvs(objs=None, uv_set=None, u=None, v=None, selection_if_none=True):
	def do_u(**kwargs):
		return not(u is None or u == 1.0)

	def do_v(**kwargs):
		return not(v is None or v == 1.0)

	def _modify_comp(x, u_or_v):
		if u_or_v == 0.0 or x == 0.0:
			return 0.0

		if x < 0.0:
			return -((-x) ** u_or_v)

		return x ** u_or_v

	def modify_u(x, **kwargs):
		return _modify_comp(x, u)

	def modify_v(x, **kwargs):
		return _modify_comp(x, v)

	return _perform_with_mesh_uvs(
		objs, uv_set, selection_if_none,
		modify_u, modify_v,
		do_u, do_v,
		u=u, v=v
	)


def _get_bbox(uvs):
	"""
	Bounding box of the given UVs. Requires UVs list to be flattened.

	:param uvs: WARNING! it has to be a flattened list of pyMel's UVs.
	:return: (min_u, min_v), (max_u, max_v)
	"""
	all_us, all_vs = zip(*[pm.polyEditUV(uv, q=1) for uv in uvs])
	return (min(all_us), min(all_vs)), (max(all_us), max(all_vs))


def bounding_box(items=None, selection_if_none=True):
	"""
	Provides boundaries for the given UVs (converts selection to UVs if necessary).
	Works only with current UV-set.

	:param items: <list> Source elements (objects/components) of a scene to be converted.
	:param selection_if_none: <bool> whether to use current selection if items is None.
	:return: <floats>: (min_u, min_v), (max_u, max_v)
	"""
	uvs = comp.Poly(items, selection_if_none=selection_if_none).to_uvs(flatten=True)
	return _get_bbox(uvs)


def _move_uvs_to_range(uvs, min_u=-1, min_v=-1, max_u=2, max_v=2, round_mode=2):
	"""
	Low-level function, transforming the given UVs to a specified UV range.
	It preserves the actual texture by moving only at integer steps.

	It works on the current UV-set, so it's your responsibility to make sure
	the given UVs are listed for the current UV-set.

	:param uvs: <list> UVs to move.\nWARNING: it's your responsibility to make sure there are only UVs in the list.
	:param min_u: <int> resulting UV-range minimum in U axis.
	:param min_v: <int> resulting UV-range minimum in V axis.
	:param max_u: <int> resulting UV-range maximum in U axis.
	:param max_v: <int> resulting UV-range maximum in V axis.
	:param round_mode: <int>, how exactly uvs will be placed if their boundary is bigger then range:
	\n 0 - rounded down (floor: if delta is odd, left-down square will be occupied);
	\n 1 - rounded up (ceil);
	\n 2 - round to nearest.
	\n When UVs fit in the range, proper round (to nearest) is used anyway.
	:return: <list> given UVs if they were moved, empty list otherwise.
	"""
	import math

	if not uvs:
		return []
	uvs_flat = pm.ls(uvs, fl=1)
	if not uvs_flat:
		return []

	def _test_arg(val):
		"""
		Ensures the given range argument is int.
		"""
		if isinstance(val, int):
			return val
		if isinstance(val, float):
			return int(round(val))
		raise err.WrongTypeError(val, var_name='one of range boundaries', types=(int, float))

	min_u, min_v, max_u, max_v = [_test_arg(x) for x in (min_u, min_v, max_u, max_v)]

	# the actual boundaries of the given UVs:
	uvs_min, uvs_max = _get_bbox(uvs_flat)

	rounding_f = [math.floor, math.ceil, round][round_mode]

	def _calc_single_offset(uvs_mi, uvs_ma, range_mi, range_ma):
		"""
		Calculates the offset for a single axis (U/V). Returns an int value.
		"""
		if uvs_mi > range_mi and uvs_ma < range_ma:
			return 0

		uvs_min_square = int(uvs_mi)
		uvs_max_square = int(math.ceil(uvs_ma))
		uvs_len_square = uvs_max_square - uvs_min_square
		range_len_square = range_ma - range_mi
		cur_round_f = round if uvs_len_square <= range_len_square else rounding_f

		uvs_center = (uvs_mi + uvs_ma) * 0.5
		range_center = (range_mi + range_ma) * 0.5
		return int(cur_round_f(range_center - uvs_center))

	offsets = [
		_calc_single_offset(u_mi, u_ma, r_mi, r_ma)
		for u_mi, u_ma, r_mi, r_ma
		in zip(uvs_min, uvs_max, (min_u, min_v), (max_u, max_v))
	]

	if all([x == 0 for x in offsets]):
		return []

	pm.polyEditUV(uvs_flat, relative=1, u=offsets[0], v=offsets[1])
	return uvs



def move_shells_to_range(
	items=None,
	min_u=-1, min_v=-1, max_u=2, max_v=2, round_mode=2,
	uv_set=None, selection_if_none=True
):
	# switch to the given UV-set if it's specified:
	uv_sets.set_current(items, uv_set, selection_if_none)

	shells = comp.uv_shells(items, selection_if_none, collapse=True)

	def _do_func(uvs, i, res):
		# assert isinstance(res, list)
		res.extend(_move_uvs_to_range(uvs, min_u, min_v, max_u, max_v, round_mode))

	return ui.ProgressWindow.do_with_each(
		shells, _do_func, 'Move UV-shells', 'Shell: {0} / {1}'
	)


def _snap_uvs_bbox_to_zero(uvs):
	min_uv, max_uv = _get_bbox(pm.ls(uvs, fl=1))
	if not any(min_uv):
		return []
	pm.polyEditUV(uvs, relative=1, u=-min_uv[0], v=-min_uv[1])
	return uvs


def snap_shells_to_zero(items=None, uv_set=None, selection_if_none=True):
	"""
	Move all the given UV-shells so that they'll be located as low and as left as possible in the main UV-square.

	I.e., snap each shell's leftmost lowest corner of a bounding box to the (0, 0) coordinate.

	:param items: <list> source objects/components (will be converted to UVs before proceeding).
	:param uv_set: <int/string> The number or the name for the UV-set. Number starts at 1. 0 or <None> means use current.
	:param selection_if_none: <bool> whether to use current selection if items is None.
	:return: <list> of UVs that were moved.
	"""

	# switch to the given UV-set if it's specified:
	uv_sets.set_current(items, uv_set, selection_if_none)

	shells = comp.uv_shells(items, selection_if_none, collapse=True)

	def _do_func(uvs, i, res):
		# assert isinstance(res, list)
		res.extend(_snap_uvs_bbox_to_zero(uvs))

	return ui.ProgressWindow.do_with_each(
		shells, _do_func, 'Move UV-shells', 'Shell: {0} / {1}'
	)
