__author__ = 'Lex Darlog (DRL)'

import maya.cmds as cmds
from ..input_warn import items_input as wrn_items

from drl_py23 import (
	str_t as _str_t,
	str_h as _str_h,
)

from . import default_input
from . import convert
from . import pymel


_t_str_or_list = tuple(list(_str_t) + [list])


def unique_sort(objects=None, **ls_args):
	"""
	Removes duplicates from the list of objects and sorts it alphabetically.
	It's also possible to apply an additional filter to this list by passing any arguments for the ls command.
	:param objects: list of objects in the scene
	:param ls_args: extra keyword-arguments passed to the Maya's <ls> function
	:return: alphabetically sorted list of unique object names.
	"""
	if not objects:
		return []
	# force all the occurrences of the same object to be written the same way:
	objects = cmds.ls(objects, **ls_args)

	objects = list(set(objects))
	objects.sort()
	return objects


def selected_highlighted(objects=None, objectsOnly=False):
	"""
	Lists all the selected and highlighted objects.
	:param objects: If objects list is given, returns those of them which are selected/highlighted
	:param objectsOnly: if True, selected components are converted to their shape names
	:return: the united list of selected/highlighted objects/components, with removed duplicates
	"""
	if objects:
		objects = cmds.ls(objects, sl=1, objectsOnly=objectsOnly)
		objects += cmds.ls(objects, hl=1, objectsOnly=objectsOnly)
	else:
		objects = cmds.ls(sl=1, objectsOnly=objectsOnly)
		objects += cmds.ls(hl=1, objectsOnly=objectsOnly)
	objects = unique_sort(objects)
	return objects


def objects_transforms(objects=None):
	"""
	Lists objects only, converting all the shapes/components to their transform nodes.
	If optional 'objects' parameter is left empty, the current selection is used,
	also taking into account highlighted objects.
	:param objects: if specified, this list of objects is processed.
	:return: list of transform node names (absolute paths if not unique)
	"""
	if not objects:
		objects = selected_highlighted(objectsOnly=True)
	if not objects:
		return []
	if isinstance(objects, str):
		objects = [objects]
	objects = list(set(objects))
	shapes = cmds.ls(objects, objectsOnly=1, shapes=1)  # objectsOnly converts components to their shapes
	objects = cmds.ls(objects, transforms=1) # in case there were components, leave only transforms
	if shapes:
		objects = list(set(objects) - set(shapes))
		shapeTransforms = cmds.listRelatives(shapes, fullPath=True, parent=True)
		objects += shapeTransforms
	# enforce uniqueness and sort alphabetically:
	objects = unique_sort(objects)
	return objects


def parent(obj=None, fullPath=False):
	"""
	Deprecated. Use Convert.Hierarchy.to_parent instead.
	"""
	from .convert import hierarchy as hrc
	return hrc.to_parents(obj, fullPath=fullPath)


def child_shapes(objects=None, allChildObjects=False):
	"""
	Lists all the child shape nodes.
	:param objects: list of root transforms names
	:param allChildObjects: If true, all the child, grandchild etc. shape nodes are returned
	:return: list of all the child shape node names
	"""
	if not objects:
		objects = selected_highlighted(objectsOnly=True)
	if not objects:
		return []
	if allChildObjects:
		objects = cmds.listRelatives(objects, fullPath=True, allDescendents=1)
	else:
		objects = cmds.listRelatives(objects, fullPath=True, children=1)
	objects = unique_sort(objects, shapes=1)
	return objects


def SGs_to_materials(SGs=None):
	if not isinstance(SGs, _t_str_or_list):
		return None
	if not SGs:
		return None
	if not isinstance(SGs, list):
		SGs = [SGs]
	return cmds.listConnections([sg + '.surfaceShader' for sg in SGs], d=0, s=1)


def materials_to_SGs(mats=None):
	if not (isinstance(mats, str) or isinstance(mats, list)):
		return None
	if not mats:
		return None
	if isinstance(mats, str):
		mats = [mats]
	return cmds.listConnections([m + '.outColor' for m in mats], d=1, s=0)


def shape_to_SGs(shapeNode=None):
	return cmds.listConnections(shapeNode, type='shadingEngine', s=0, d=1)


def assigned_materials(shapeNode=None, **ls_args):
	"""
	Lists materials assigned to the object's shape node.
	:param shapeNode: shape node of the object
	:return: list of assigned materials
	"""
	SGs = shape_to_SGs(shapeNode)
	if not SGs:
		return []
	SGs = unique_sort(SGs, **ls_args)
	return {
		'SGs': SGs,
		'mats': SGs_to_materials(SGs)
	}


def assigned_mat_to_face(face=None, SGs=None):
	"""
	Returns the material assigned to face.
	You can significantly speed up this function
	by providing a list of SGs for the shape node this face is part of.
	:param face:
	:param SGs:
	:return: dictionary with 2 string elements: SG and mat
	"""
	if not SGs:
		shapeNode = cmds.ls(face, objectsOnly=1, shapes=1)  # objectsOnly converts components to their shapes
		SGs = shape_to_SGs(shapeNode)
	if not SGs:
		return None
	assigned_SG = None
	for sg in SGs:
		if cmds.sets(face, isMember=sg):
			assigned_SG = sg
			break
	return {
		'SG': assigned_SG,
	  'mat': SGs_to_materials(assigned_SG)[0]
	}


def objects_by_material(objects=None):
	"""
	Returns dictionary of lists, in which the given objects are grouped by their material.
	Only 1st material for the object is used, only 1st shape of the object checked.
	:param objects: list of objects
	:return: dictionary, in which keys are material names and values are lists of objects using it
	"""
	if not objects:
		return {}
	objs = objects_transforms(objects)
	if not objs:
		return {}
	res = {}
	for o in objs:
		shape = child_shapes([o])
		if shape:
			shape = shape[0]
			mat = assigned_materials(shape)['mats']
			if mat:
				mat = mat[0]
				if not mat in res:
					res[mat] = list()
				res[mat].append(o)
	return res


def shapes_to_materials(shapes=None, **ls_args):
	"""
	For the given list of shapes list the assigned materials.

	:param shapes: list of shape nodes
	:param ls_args: optional arguments passed to the ls command
	:return: list of the material nodes
	"""
	shapes = wrn_items(shapes, stacklevel_offset=1)
	if not shapes:
		return []
	res = []
	for s in shapes:
		res += assigned_materials(s, **ls_args)['mats']
	return res


def objects_to_materials(objects=None, allChildObjects=False, **ls_args):
	"""
	High-level function, allowing to get the list of material nodes, assigned to the given objects.

	:param objects: objects to check
	:param allChildObjects: whether all the child, grandchild etc shape nodes are checked
	:param ls_args: optional arguments passed to the ls command
	:return: list of material nodes
	"""
	shapes = child_shapes(objects, allChildObjects=allChildObjects)
	return shapes_to_materials(shapes, **ls_args)