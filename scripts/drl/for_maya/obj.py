import os
import re
import maya.cmds as cmds

def batchImp(path):
	'''
			Batch OBJ import
Imports all the OBJ files found at the specified folder.
Especially useful for importing Zbrush's subtools (let's say, for UV-mapping).
Imported objects are named by filenames.
	'''
	res = []
	if os.path.isdir(path):
		files = os.listdir(path)
		OBJs = []
		for f in files:
			filepath = os.path.join(path, f)
			splitFile = os.path.splitext(f)

			if splitFile[-1][1:].lower()=='obj' and os.path.isfile(filepath):
				created = cmds.file(filepath,
														i=True,
														type='OBJ',
														rdn=True,
														rpr=splitFile[0],
														options='mo=0',
														pr=True,
														loadReferenceDepth='all',
				#										gr=True,
				#										gn=splitFile[0],
														rnn=True # return names of created nodes
				)
				created = cmds.ls(created, fl=True, g=True, l=True) # filter out everything except for mesh-shapes
				for i in range(len(created)):
					created[i] = cmds.listRelatives(created[i], p=True, f=True)[0] # get object themselves (transforms)
					created[i] = cmds.rename(created[i], splitFile[0])
					res.append(created[i])
					print(res[-1])
	return res

# --------------------------------------------------------------------------------------------------------------------

def batchImpMA(path):
	'''
			Batch MA import
Imports all the OBJ files found at the specified folder.
Especially useful for importing Zbrush's subtools (let's say, for UV-mapping).
Imported objects are named by filenames.
	'''
	res = []
	if os.path.isdir(path):
		files = os.listdir(path)
		OBJs = []
		for f in files:
			filepath = os.path.join(path, f)
			splitFile = os.path.splitext(f)

			if splitFile[-1][1:].lower()=='ma' and os.path.isfile(filepath):
				created = cmds.file(filepath,
														i=True,
														type='mayaAscii',
														rdn=True,
														mergeNamespacesOnClash=False,
														rpr=splitFile[0],
														options='v=1;',
														pr=True,
														loadReferenceDepth='all',
				#										gr=True,
				#										gn=splitFile[0],
														rnn=True # return names of created nodes
				)
				created = cmds.ls(created, fl=True, g=True, l=True) # filter out everything except for mesh-shapes
				for i in range(len(created)):
					created[i] = cmds.listRelatives(created[i], p=True, f=True)[0] # get object themselves (transforms)
					created[i] = cmds.rename(created[i], splitFile[0])
					res.append(created[i])
					print(res[-1])
	return res

# --------------------------------------------------------------------------------------------------------------------

def batchImpMB(path):
	'''
			Batch MB import
Imports all the OBJ files found at the specified folder.
Especially useful for importing Zbrush's subtools (let's say, for UV-mapping).
Imported objects are named by filenames.
	'''
	res = []
	if os.path.isdir(path):
		files = os.listdir(path)
		OBJs = []
		for f in files:
			filepath = os.path.join(path, f)
			splitFile = os.path.splitext(f)

			if splitFile[-1][1:].lower()=='mb' and os.path.isfile(filepath):
				created = cmds.file(filepath,
														i=True,
														type='mayaBinary',
														rdn=True,
														mergeNamespacesOnClash=False,
														rpr=splitFile[0],
														options='v=0;',
														loadReferenceDepth='none',
				#										gr=True,
				#										gn=splitFile[0],
														rnn=True # return names of created nodes
				)
				created = cmds.ls(created, fl=True, g=True, l=True) # filter out everything except for mesh-shapes
				for i in range(len(created)):
					created[i] = cmds.listRelatives(created[i], p=True, f=True)[0] # get object themselves (transforms)
					created[i] = cmds.rename(created[i], splitFile[0])
					res.append(created[i])
					print(res[-1])
	return res

# --------------------------------------------------------------------------------------------------------------------

def batchExp(OBJs=[],
						 path='',
						 pre='',
						 post='',
						 toDash=True,
						 triang=False,
						 soft=False
):
	'''
			Batch OBJ export
Exports each selected object as separate OBJ.
As a first step, cleans any history if it's there.
Also allows to change the names of the exported files by adding prefix, postfix and replacing
all non-alphanumeric characters with dashes.
Returns the array of created filepaths.
	'''
	if os.path.isdir(path):
		res = []
		if len(OBJs):
			nObj = OBJs
		else:
			nObj = cmds.ls(sl=True, fl=True, tr=True)
		for o in nObj:
			cmds.select(o, r=True)
			dup = cmds.duplicate(rr=True)[0]
			if cmds.listRelatives(dup, p=True):
				dup = cmds.parent(w=True)[0]

			nm = o.split('|')[-1] # get the short name of the object in case it's not
			nm = nm.split(':')[-1] # remove a namespace if it's there

			nm = pre + nm + post
			nm = re.sub('[^a-zA-Z_0-9]', '_', nm)
			if toDash:
				nm = re.sub('_', '-', nm)

			dup = cmds.rename(dup, nm)

			cmds.select(dup, r=True)
			cmds.makeIdentity(apply=True, t=True, r=True, s=True, n=0) # freeze transform
			# like if we were pressed 1 on keyboard:
			cmds.displaySmoothness(divisionsU=0, divisionsV=0, pointsWire=4, pointsShaded=1, polygonObject=1)
			cmds.subdivDisplaySmoothness(smoothness=1)
			cmds.select(dup, r=True)

			if triang:
				cmds.polyTriangulate(constructionHistory=False)
				cmds.select(dup, r=True)

			if soft:
				cmds.polySoftEdge(a=180, ch=False)
				cmds.select(dup, r=True)

			cmds.delete(ch=True)
			res.append(os.path.join(path, nm+'.obj'))
			cmds.file(res[-1],
								op='groups=1;ptgroups=1;materials=0;smoothing=1;normals=1',
								typ='OBJexport',
								preserveReferences=False,
								exportSelected=True
			)
			cmds.select(dup, r=True)
			cmds.delete()
		return res
	else: return []

# --------------------------------------------------------------------------------------------------------------------

def zbExp(OBJs=[], path=''):
	'''
			Batch export to Zbrush
This procedure is supposed to work with result of batchImp procedure.
It exports all the imported OBJs back, preserving all polygroups.
	'''
	res = []
	OK = False
	if os.path.exists(path):
		if os.path.isdir(path):
			OK = True
	else:
		os.makedirs(path)
		OK = True

	nObj = OBJs
	if not len(nObj):
		nObj = cmds.ls(sl=True, fl=True, tr=True)
		if not len(nObj):
			nObj = cmds.ls(fl=True, g=True)
			for i in range(len(nObj)):
				nObj[i] = cmds.listRelatives(nObj[i], p=True, f=True)[0] # get object themselves (transforms)
	nObj = list(set(nObj))

	if OK:
		for o in nObj:
			filepath = os.path.join(path, o)
			if not ( os.path.exists(filepath) and not os.access(filepath, os.W_OK) ): # check if we can export
				cmds.select(o, r=True)
				cmds.delete(ch=True)
				filepath = cmds.file(filepath,
									op='groups=1;ptgroups=1;materials=0;smoothing=1;normals=1',
									typ='OBJexport',
									preserveReferences=False,
									exportSelected=True
				)
				res.append(filepath)
				print(filepath)
	return res