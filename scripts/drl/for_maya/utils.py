from drl_common import errors as err

__author__ = 'Lex Darlog (DRL)'

import warnings as wrn

import maya.cmds as cmds

from . import ls

hrc = ls.convert.hierarchy
lsd = ls.default_input
no_sel = dict(selection_if_empty=False)



def make_transform_path(path=None):
	"""
	Ensures the existence of the given path. Extra transforms are created if needed.
	:param path: string absolute path
	:return: Last
	"""
	err.NotStringError(path, 'path').raise_if_needed()
	path = path.strip('|').split('|')
	if path == ['']:
		path = []
	cur_path = ''
	parent = ''
	selected = cmds.ls(sl=1)
	for p in path:
		create_group=False
		cur_path += '|' + p
		if not cmds.ls(cur_path):
			# path doesn't exist
			create_group = True
		elif not cmds.ls(cur_path, type='transform'):
			# exists, but it's not transform
			cmds.rename(cur_path, p + '_old')
			create_group = True

		if create_group:
			args = dict(name=p, empty=True)
			if not parent:
				# we're creating 1st to_parent, i.e., we're in world
				args['world'] = True
			else:
				# we're already inside hierarchy
				args['to_parent'] = parent
			parent = cmds.group(**args)
			parent = hrc.to_full_paths(parent, **no_sel)[0]
		else:
			parent = cur_path
	if selected: cmds.select(selected, r=1)
	if parent:
		return parent
	return ''



def reparent_to_world(objects=None, selection_if_empty=True):
	"""
	Parents the objects to the world. Without error, if objects are already in the world.
	:param objects:
	:param selection_if_empty:
	:return:
	"""
	objects = hrc.to_full_paths_unique(objects, selection_if_empty=selection_if_empty)
	for i, o in enumerate(objects):
		if hrc.to_parents(o, **no_sel):
			nu_path = cmds.parent(o, w=True)[0]
			nu_path = hrc.to_full_paths(nu_path, **no_sel)[0]
			objects[i] = nu_path
	return objects



def reparent_to_path(objects=None, parent=None, selection_if_empty=True):
	parent = make_transform_path(parent)
	if not parent:
		return reparent_to_world(objects, selection_if_empty=selection_if_empty)
	objects = hrc.to_full_paths_unique(objects, selection_if_empty=selection_if_empty)
	if objects:
		objects = cmds.parent(objects, parent)
	return objects



def duplicate_to_world_group(objects=None, groupName='group'):
	from .fix_default import select
	from drl_common.utils import remove_duplicates

	if not groupName:
		msg = '\nEmpty string given as <groupName> argument.'
		wrn.warn(msg, RuntimeWarning, stacklevel=2)
		return []
	curSel = cmds.ls(sl=1, long=1)
	if not objects:
		objs = curSel[:]
	else:
		objs = remove_duplicates( cmds.ls(objects, long=1) )
	if not objs:
		msg = '\nNo objects selected.'
		wrn.warn(msg, RuntimeWarning, stacklevel=2)
		return []

	group = '|' + groupName
	if not cmds.ls(group):
		cmds.select(cl=1)
		cmds.group(n=groupName, w=1, empty=1)
	elif not cmds.ls(group, tr=1):
		msg = '\nThe given <groupName> is already in the scene but is not a transfrom node.'
		wrn.warn(msg, RuntimeWarning, stacklevel=2)
		return []

	select(objs, r=1)
	cmds.duplicate(rr=1)
	duplicates = cmds.ls(sl=1, long=1)
	duplicates = cmds.parent(duplicates, group)

	return duplicates


def get_modifiers():
	'''
	More user-friendly function, returning the state (on/off) of modifier keys.
	:return: dictionary with elements: shift, ctrl, alt
	'''
	mods = cmds.getModifiers()

	def perform(bit):
		if (mods & bit) > 0: return True
		return False

	return {
		'shift': perform(1),
		'ctrl': perform(4),
		'alt': perform(8)
	}