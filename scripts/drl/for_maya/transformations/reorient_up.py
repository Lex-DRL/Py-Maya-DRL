__author__ = 'DRL'

from pymel import core as _pm
from drl.for_maya.ls import pymel as _ls


def __reorient_up(root_objects, selection_if_none=True, rotate_x=-90):
	root_objects = _ls.to_objects(
		root_objects, selection_if_none, remove_duplicates=True
	)
	if not root_objects:
		return list()
	# root_objects = [
	# 	x for x in _pm.ls(type='joint')
	# 	if not _pm.listRelatives(x, p=1)
	# ]
	group = _pm.group(root_objects, w=1)
	_pm.rotate(group, (rotate_x, 0, 0), pivot=(0, 0, 0), ws=1)
	_pm.ungroup(group, w=1)
	return root_objects


def z_to_y(objects=None, selection_if_none=True):
	return __reorient_up(objects, selection_if_none)


def y_to_z(objects=None, selection_if_none=True):
	return __reorient_up(objects, selection_if_none, 90)
