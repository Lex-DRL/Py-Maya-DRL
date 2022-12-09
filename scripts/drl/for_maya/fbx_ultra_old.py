__author__ = 'Lex Darlog (DRL)'

import shutil as sh
import warnings as wrn

from drl.for_maya.fbx_old import *

from drl.for_maya import fix_default as fix
from drl.for_maya import layers as lrs
from drl.for_maya import ls

from maya import cmds, mel


def perform_combine_by_material(objects=None, prefix='', postfix=''):
	objs = cmds.listRelatives(objects, fullPath=1, allDescendents=1)
	objs = ls.unique_sort(objs)
	matObj = ls.objects_by_material(objects)
	res = []
	for mat, objs in matObj.items():
		if len(objs) < 2:
			combined = fix.duplicate(objs[0], rr=1)
			if cmds.listRelatives(combined, fullPath=1, allParents=1):
				combined = cmds.parent(combined, w=1)[0]
		else:
			combined = fix.duplicate(objs, rr=1)
			combined = cmds.polyUnite(combined, ch=0)[0]
		combined = cmds.rename(combined, prefix + mat + postfix)
		res.append(combined)
	return res


def perform_export_for_layers(objects=None, layers=None, exportDir='', presetFilePath='', combineByMaterial=False):
	'''
	Exports given list of layers as separate FBX files into the given path.
	:param layers: list of layer names to export
	:param exportDir: the path to export
	:param presetFilePath:the path to FBX export preset that is used
	:return: dictionary, in which keys are base filenames, values are exported filepaths
	'''
	if not objects:
		selObjs = cmds.ls(sl=1)
	elif not( type(objects)==type([]) or type(objects)==type('') ):
		msg = '\n<objects> parameter needs to be a list of objects.'
		wrn.warn(msg, RuntimeWarning, stacklevel=3)
		return {}
	else:
		selObjs = cmds.ls(objects)

	if not selObjs:
		msg = '\nNo objects selected.'
		wrn.warn(msg, RuntimeWarning, stacklevel=3)
		return {}

	fix.select(selObjs, r=1, hierarchy=1)
	selObjs = cmds.ls(sl=1, l=1)

	exports = {}
	for lr in layers:
		objs = cmds.editDisplayLayerMembers(lr, q=1, fullNames=1)  # objects in layer
		objs = ls.child_shapes(objs, allChildObjects=1)
		objs = ls.objects_transforms(objs)
		fix.select(selObjs, r=1)
		objs = cmds.ls(objs, sl=1)
		objs = ls.unique_sort(objs)
		if objs:
			fbxFile = os.path.join(exportDir, lr) + '.fbx'
			fbxFile = fbxFile.replace('\\', '/')
			fs.clean_path_for_file(fbxFile, overwrite_folders=1, remove_file=1)
			if combineByMaterial:
				objs = perform_combine_by_material(objs, prefix=(lr + '_'))
			cmds.select(objs, r=1)
			mel.eval('FBXLoadExportPresetFile -f "%s"' % presetFilePath)
			mel.eval('FBXExport -s -f "%s"' % fbxFile)
			exports[lr] = fbxFile
			if combineByMaterial:
				cmds.delete(objs)
	return exports


def perform_move_files_to_final_dir(exports={}, exportDir=''):
	'''
	Performs safe move of files to the specified dir, avoiding any errors.
	:param exports: in which keys are base filenames, values are exported filepaths
	:param exportDir: directory to which the exported files need to be moved to
	:return: tuple: (
		list of successfully moved files,
		dictionary with keys:
			dir: list of files that were unable to move because the target path is already taken by folder
			undel: list of files that were unable to replace with the new ones
	)
	'''
	err = {
		'dir': [],
		'undel': []
	}
	moved = list()
	for bs, fl in exports.items():
		nuFl = os.path.join(exportDir, bs + '.fbx')
		nuFl = nuFl.replace('\\', '/')
		if os.path.isdir(nuFl):
			err['dir'].append(nuFl)
		else:
			fs.clean_path_for_file(nuFl, overwrite_folders=1, remove_file=1)
			if os.path.isdir(nuFl) or os.path.isfile(nuFl) or os.path.islink(nuFl):
				err['undel'].append(nuFl)
			else:
				sh.move(fl, nuFl)
				moved.append(nuFl)
	return moved, err

def export_by_layer(
	objects=None,
	exportDir=r'E:\5-Internet\Downloads\000',
	presetName='User defined',
	combineByMaterial=False
):
	if not exportDir:
		msg = "\nThe path for export is unspecified."
		wrn.warn(msg, RuntimeWarning, stacklevel=2)
		return []
	elif os.path.isfile(exportDir):
		msg = "\nUnable to export because the given path is already taken by the file, not a folder."
		wrn.warn(msg, RuntimeWarning, stacklevel=2)
		return []
	fs.clean_path_for_folder(exportDir, overwrite=2)

	presetFile = Preset(presetName).path()
	if not presetFile:
		msg = "\nThe specified FBX export preset is not found."
		wrn.warn(msg, RuntimeWarning, stacklevel=2)
		return []

	layers = lrs.selected_with_warning(display=1, stacklevel=3)

	projDir = cmds.workspace(q=1, fullName=1)
	# projDir = 'E:/1-Projects/Maya/ssTrapsSrc'
	if not projDir:
		msg = '\nThe project directory is unspecified, please set the project first.'
		wrn.warn(msg, RuntimeWarning, stacklevel=2)
		return []

	curSel = cmds.ls(sl=1)
	tempDir = os.path.join(projDir, 'DRL_FBX_tmp')
	tempDir = tempDir.replace('\\', '/')
	fs.clean_path_for_folder(tempDir, overwrite=2)

	# export layer-by-layer:
	exports = perform_export_for_layers(objects, layers, tempDir, presetFile, combineByMaterial)
	# move exported files to final destination:
	moved, err = perform_move_files_to_final_dir(exports, exportDir)

	if err['dir']:
		print('\n\n\n\tUnable to move the following files, because these paths are already taken by folders:')
		for d in err['dir']:
			print(d)
	if err['undel']:
		print('\n\n\n\tUnable to replace the following files with the new ones:')
		for u in err['undel']:
			print(u)
	if err['dir'] or err['undel']:
		msg = "\nSome exported files are failed to move to the destination directory. They're left in the following folder:\n" \
					"%s" \
					"\nSee Script Editor for details." % tempDir
		wrn.warn(msg, RuntimeWarning, stacklevel=2)
	if not os.listdir(tempDir):
		sh.rmtree(tempDir)
	if curSel:
		cmds.select(curSel, r=1)
	return moved