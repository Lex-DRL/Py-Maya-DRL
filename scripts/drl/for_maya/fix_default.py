__author__ = 'DRL'

import maya.cmds as cmds

def select(*args, **kwargs):
	'''
	Fail-safe select command. Doesn't return any errors if there's no objects given.
	:param args: objects to select
	:param kwargs: keyword-arguments passed to the Maya's select command
	:return: None
	'''
	if not kwargs:
		kwargs = dict(r=True)

	if \
		('r' in kwargs.keys() and kwargs['r']) or \
		('replace' in kwargs.keys() and kwargs['replace']) or \
		('cl' in kwargs.keys() and kwargs['cl']) or \
		('clear' in kwargs.keys() and kwargs['clear']):
			cmds.select(cl=True)

	if \
		('all' in kwargs.keys() and kwargs['all']) or \
		('adn' in kwargs.keys() and kwargs['adn']) or \
		('allDependencyNodes' in kwargs.keys() and kwargs['allDependencyNodes']) or \
		('ado' in kwargs.keys() and kwargs['ado']) or \
		('allDagObjects' in kwargs.keys() and kwargs['allDagObjects']):
			cmds.select(**kwargs)
			return

	args = tuple(a for a in args if a != '' and a != [])

	if args and kwargs:
		cmds.select(*args, **kwargs)

def duplicate(*objects, **kwargs):
	from drl_common.utils import remove_duplicates
	curSel = cmds.ls(sl=1)
	res = []
	for o in objects:
		select(o, r=1)
		cmds.duplicate(**kwargs)
		res += cmds.ls(sl=1, long=1)
	res = remove_duplicates(res)
	res = cmds.ls(res)
	select(curSel, r=1)
	return res