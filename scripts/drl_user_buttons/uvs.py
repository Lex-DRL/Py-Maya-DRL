__author__ = 'DRL'

from pymel import core as _pm

from drl_common.py_2_3 import reload
from drl.for_maya import ui as _ui
from drl.for_maya.geo.components import (
	uvs as _uvs,
	uv_sets as _uv_sets,
)
reload(_ui)
reload(_uvs)
reload(_uv_sets)


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


def select_by_set(exclude=False):
	"""Filter selected objects based on whether they have the given UV-set."""
	set_name = _ui.dialog_str(
		'Sel by UV-set',
		"DOESN'T have this uv-set:" if exclude else 'HAS this uv-set:',
		'map1'
	)
	if not set_name:
		return
	res = _uv_sets.filter_by_set(None, True, set_name, exclude)
	_pm.select(res, r=1)
