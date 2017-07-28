__author__ = 'DRL'


from pymel import core as pm
from drl.for_maya.ls import pymel as ls
from drl.for_maya.ui import ProgressWindow
from drl_common import errors as err

from drl.for_maya import py_node_types as _pnt
_t_transform = _pnt.transform


def freeze_transform(
	items=None, selection_if_none=True,
	translate=True, t=None,
	rotate=True, r=None,
	scale=True, s=None,
	normals=0, n=None,
	joint_orient=True, j=None
):
	"""
	Wrapper for standard Maya Freeze transform.
	Short versions of arguments override the long ones, when not None.

	:param items: objects to perform freeze transform for. If components/shapes selected, they're converted to their Transform.
	:param selection_if_none: whether to use selection when no items given.
	:param translate / t: freeze the actual transform (offset).
	:param rotate / r: freeze rotation.
	:param scale / s: freeze scale.
	:param normals / n: whether to lock normals:
	* 0 - Never
	* 1 - Always
	* 2 - if object has non-rigid transformations. I.e., a transformation that does not contain shear, skew or non- proportional scaling.
	:param joint_orient / j: Whether the joint orient on joints will be reset to align with world-space.
	:return: <list of PyNodes> processed objects. No duplicates, even if components were selected.
	"""
	items = ls.to_objects(items, selection_if_none, remove_duplicates=True)

	def _single_arg(main, short):
		if not (short is None):
			return short
		return main

	kw_args = dict(
		apply=True, preserveNormals=True,
		translate=_single_arg(translate, t),
		rotate=_single_arg(rotate, r),
		scale=_single_arg(scale, s),
		normal=_single_arg(normals, n),
		jointOrient=_single_arg(joint_orient, j)
	)
	pm.makeIdentity(items, **kw_args)
	return items


def freeze_pivot(
	items=None, selection_if_none=True,
	clean_rotate=False, clean_scale=False, progressbar_after=10
):
	"""
	Fixes the mesh, moving it's transform to the pivot.
	I.e., forces the mesh's pivot to be at (0,0,0) in local space, keeping the appearance of the surface intact.

	:param items: items (objects/components) to snap. The same order expected.
	:param selection_if_none: whether to use selection when no items given.
	:param clean_rotate: when True, the resulting mesh will also have it's ROTATE "frozen" to (0,0,0)
	:param clean_scale: when True, the resulting mesh will also have it's SCALE "frozen" to (0,0,0)
	:return: the list of objects that had non-zero pivot offset and therefore were transformed/cleaned up
	"""
	items = ls.default_input.handle_input(items, selection_if_none, flatten=False)
	# extra check here to prevent getting all the transforms later:
	if not items:
		return []

	items = pm.ls(items, tr=1)
	if not items:
		return []
	# now we have only transforms in the list

	freeze_kwargs = dict(
		apply=True,
		jointOrient=True,
		normal=2,
		translate=True,
		rotate=clean_rotate,
		scale=clean_scale
	)


	def _clean_single(obj):
		err.WrongTypeError(obj, (str, unicode, _t_transform), 'object').raise_if_needed()
		pivot_pos = pm.xform(obj, q=1, worldSpace=1, rotatePivot=1)
		offset = pivot_pos[:]
		parent = ls.to_parent(obj, False)  # always returns list
		if parent:
			parent_pos = pm.xform(parent[0], q=1, worldSpace=1, translation=1)
			offset = map(lambda pr, pv: pv - pr, parent_pos, pivot_pos)

		if not any(
			offset +  # lists concatenation:
			map(
				lambda piv, pos: piv - pos,
				pivot_pos,
				pm.xform(obj, q=1, worldSpace=1, translation=1)
			)
		):
			return []

		neg_offset = [-x for x in offset]
		pm.move(obj, neg_offset, r=1, ws=1)
		pm.makeIdentity(obj, **freeze_kwargs)
		pm.move(obj, offset, r=1, ws=1)
		return [obj]

	res = []

	num = len(items)
	if num > max(progressbar_after, 1):
		ProgressWindow('0 / %s' % num, 'Transform -> Pivot', max=num)
		i = 0
		while ProgressWindow.is_active():
			itm = items[i]
			msg = '{0} / {1}: {2}'.format(i + 1, num, itm.name())
			print msg
			ProgressWindow.message = msg
			res += _clean_single(itm)
			i += 1
			ProgressWindow.increment()
	else:
		for itm in items:
			res += _clean_single(itm)

	return res


def reset_pivot(items=None, selection_if_none=True):
	"""
	Reset pivots for the given objects. I.e., set them to 0 in object space.
	:param items: objects to perform freeze transform for. If components/shapes selected, they're converted to their Transform.
	:param selection_if_none: whether to use selection when no items given.
	:return: <list of PyNodes> processed objects. No duplicates, even if components were selected.
	"""
	items = ls.to_objects(items, selection_if_none, remove_duplicates=True)
	items = [x for x in items if isinstance(x, _t_transform)]
	map(lambda t: t.setPivots((0, 0, 0), objectSpace=1), items)
	return items


def instance_to_object(objects=None, selection_if_none=True):
	"""
	Converts an instanced object to a "normal" one.

	:param objects: source
	:param selection_if_none: whether to use selection if <objects> is None
	:return: list of PyNodes. It contains both converted and intact objects.
	"""
	objects = ls.default_input.handle_input(objects, selection_if_none)
	res = list()

	def is_instanced(shape):
		parents = pm.listRelatives(shape, allParents=1)
		return len(parents) > 1

	for o in objects:
		shapes = pm.listRelatives(o, shapes=1)
		if not shapes or any(map(is_instanced, shapes)):
			res.append(o)
			continue
		dup = pm.duplicate(o)[0]
		nm = o.name()
		pm.delete(o)
		dup = pm.rename(dup, nm)
		res.append(dup)
	return res


def un_parent(items=None, selection_if_none=True):
	"""
	Error-safe un-parent to world. I.e., even if object is already in world, no error is thrown.

	:param items: objects to perform freeze transform for. If components/shapes selected, they're converted to their Transform.
	:param selection_if_none: whether to use selection when no items given.
	:return: <list of PyNodes> processed objects. No duplicates, even if components were selected.
	"""
	items = ls.to_objects(items, selection_if_none, remove_duplicates=True)

	def _un_parent_single(obj):
		if not pm.listRelatives(obj, parent=1):
			return obj
		return pm.parent(obj, world=1)[0]

	return [_un_parent_single(o) for o in items]