__author__ = 'DRL'

from pymel import core as _pm

from drl.for_maya.geo.components import uvs as _uvs
reload(_uvs)


def to_square_map1():
	return _uvs.move_shells_to_range(uv_set=1, min_u=0, min_v=0, max_u=1, max_v=1)


def to_square_lm():
	return _uvs.move_shells_to_range(uv_set='LM', min_u=0, min_v=0, max_u=4, max_v=1)


def get_pos():
	return _pm.polyEditUV(q=1)


def snap_shells_to_zero(select=True):
	res = _uvs.snap_shells_to_zero()
	if res and select:
		_pm.select(res, r=1)
	return res