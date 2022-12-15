__author__ = 'Lex Darlog (DRL)'

import warnings as wrn

import maya.cmds as cmds
from drl.for_maya import layers as lrs
from drl.for_maya import ls

def moveShells_toNormalSquare(objects=None):
	if not type(objects) == type([]):
		msg = '\n<objects> parameter needs to be a list of objects.'
		wrn.warn(msg, RuntimeWarning, stacklevel=2)
		return
	# list of uvs, one item per object
	objUVs = cmds.polyListComponentConversion(objects, tuv=1)
	for UVs in objUVs:
		pass

def atlas(objects=None, groupName='Atlased_UVs', numU = 4, numV = 4):
	'''
	Combines all the UVs for the given objects to the same texture atlas, based on their materials.

	:param objects: list of objects to combine. Their UVs already need to be normalized (lay in [0-1] square)
	:param groupName: optional broup name where atlased copies will be placed
	:param numU: number of cells per U
	:param numV: number of cells per U
	:return: list of atlased objects
	'''
	from drl.for_maya.utils import duplicate_to_world_group
	from drl.for_maya.fix_default import select
	from math import floor

	if not objects:
		objs = lrs.selected_to_objects()
	elif not( isinstance(objects, list) or isinstance(objects, str) ):
		msg = '\n<objects> parameter needs to be a list of objects.'
		wrn.warn(msg, RuntimeWarning, stacklevel=2)
		return []
	elif type(objects) == type(''):
		objs = [objects]
	else:
		objs = objects[:]

	objs = ls.objects_transforms(objs)
	if not objs:
		msg = '\nNo objects selected.'
		wrn.warn(msg, RuntimeWarning, stacklevel=2)
		return []
	objs = duplicate_to_world_group(objs, groupName=groupName)
	materials = ls.objects_to_materials(objs, allChildObjects=1, long=1)
	materials = ls.unique_sort(materials)

	sizeU = 1.0 / numU
	sizeV = 1.0 / numV
	curCell = 0

	layer_polys = cmds.polyListComponentConversion(objs, tf=1)
	layer_polys = ls.unique_sort(layer_polys)
	for mat in materials:
		cmds.hyperShade(objects=mat)
		mat_polys = cmds.polyListComponentConversion(tf=1)
		if mat_polys:
			curCellV = int(floor(curCell / float(numU)))
			curCellU = int(curCell % float(numU))
			cmds.select(mat_polys, r=1)
			mat_polys = cmds.ls(layer_polys, sl=1)
			mat_polys = ls.unique_sort(mat_polys)
			mat_uvs = cmds.polyListComponentConversion(mat_polys, tuv=1)
			cmds.polyEditUV(mat_uvs, pu=0, pv=1, su=sizeU, sv=sizeV)
			cmds.polyEditUV(mat_uvs, u=sizeU*curCellU, v=-sizeV*curCellV)
			curCell += 1
	select(objs, r=1)
	return objs