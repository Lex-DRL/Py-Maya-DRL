__author__ = 'Lex Darlog (DRL)'

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


def __get_root_joints():
	"""
	Finds all the root joints in the scene.
	They're considered as root if they don't have any parent
	or their parent is not a joint.
	:return: list of joints
	"""
	all_joints = _pm.ls(type='joint')
	return [
		x for x in all_joints
		if not any(
			isinstance(p, _pm.nt.Joint) for p in _pm.listRelatives(x, parent=1)
		)
	]


def fix_imported_dae():
	roots = __get_root_joints()
	for r in roots:
		_pm.cutKey(r, animation='keysOrObjects', clear=1)  # remove any animation on root joints

	# process root joints' parent transforms:
	parent_transforms = set(x for x in _pm.listRelatives(roots, parent=1))
	for p in parent_transforms:
		p.attr('scaleX').set(1)
		p.attr('scaleY').set(1)
		p.attr('scaleZ').set(1)
		attr = p.attr('rotateX')
		attr.set(attr.get() - 90)
		child_shapes = set(_pm.listRelatives(p, shapes=1))
		children = [
			x for x in _pm.listRelatives(p, children=1)
			if x not in child_shapes
		]
		_pm.parent(children, w=1)
		_pm.delete(p)

	# create temporary empty transform object:
	compensator = _pm.group(w=1, empty=1, n='drl_tmp_rot_compensator')
	comp_rot_attr = compensator.attr('rotateX')
	comp_rot_attr.set(-90)  # orient it accordingly to joints...
	constraints = [  # ... to constrain them to it
		_pm.parentConstraint(compensator, r, maintainOffset=1, weight=1)
		for r in roots
	]
	comp_rot_attr.set(0)  # ... and restore proper rotation value
	_pm.delete(constraints)
	_pm.delete(compensator)
	_pm.select(cl=1)
