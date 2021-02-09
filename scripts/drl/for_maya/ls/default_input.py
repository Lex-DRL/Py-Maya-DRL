"""
Provides common listing methods ensuring behavior in functions.
"""
__author__ = 'DRL'

import maya.cmds as cmds

from drl_common import errors as err


def items_list(items=None):
	"""
	Performs error-check and forcefully converts provided value to list of items (objects/nodes/components).
	:param items: Elements of a scene to be converted to standard format.
	:return: list of strings
	"""
	if items is None or not items:
		return []
	if isinstance(items, (tuple, set)):
		items = list(items)
	elif isinstance(items, (str, unicode)):
		items = [items]
	elif isinstance(items, dict):
		res = list()
		for k, v in items.items():
			res += items_list(v)
		items = res
	err.WrongTypeError(items, list, 'items', 'list of strings').raise_if_needed()
	return items


def items_list_in_scene(items=None, **ls_args):
	"""
	Performs error-check and forcefully converts provided value to list of scene elements (objects/nodes/components).
	:param items: Elements of a scene to be converted to standard format.
	:param ls_args: Arguments for maya's ls command can be provided to limit the listing.
	:return: list of strings
	"""
	items = items_list(items)
	items = cmds.ls(items, **ls_args)
	if not items:
		return []
	return items


def selection_if_empty(items=None, **ls_args):
	"""
	Performs check if the given list is the list of objects in the scene.
	And if it's not or is empty, returns current selection.
	:param items: Elements of a scene to be checked.
	:param ls_args: Arguments for maya's ls command can be provided to limit the listing.
	:return: List of strings with object paths. Empty list if no proper objects is provided and nothing selected.
	"""
	if items:
		items = items_list_in_scene(items, **ls_args)
	else:
		items = selection(**ls_args)
	return items


def selection_if_empty_f(use_selection=True):
	"""
	Service method. If argument is true, returns <selection_if_empty> function. Othwerwise, <items_list_in_scene>.
	"""
	if use_selection:
		f = selection_if_empty
	else:
		f = items_list_in_scene
	return f


def selection(**ls_args):
	"""
	Lists current selection. Returns it in standard format.
	:param ls_args: Arguments for maya's ls command can be provided to limit the listing.
	:return: List of strings with items' names. Empty list if nothing selected.
	"""
	items = cmds.ls(sl=1, **ls_args)
	items = items_list(items)
	return items