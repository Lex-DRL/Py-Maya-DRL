"""
Provides various methods allowing to convert one hierarchical entity to another.
"""
__author__ = 'Lex Darlog (DRL)'

import maya.cmds as cmds
from drl_common import errors as err
from ..import default_input


def listRel_args(main_args, fullPath=True, **extra_args):
	"""
	Service method easily producing arguments list for Maya's listRelatives function.
	:param main_args: Dictionary with primary arguments: which kind of relative to query.
	:param fullPath: Whether to return full absolute path instead of minimally unique name.
	:param extra_args: You can provide some extra arguments.
	:return: dictionary with keyword arguments.
	"""
	err.WrongTypeError(main_args, dict, 'main_args').raise_if_needed()
	new_args = main_args.copy()
	if fullPath:
		new_args['fullPath'] = True
	else:
		new_args['path'] = True
	# merge generated args and provided ones, with priority to generated
	new_args = dict(extra_args.items() + new_args.items())
	return new_args


def to_shapes(items=None, selection_if_empty=True, convert=False):
	"""
	Converts given list of objects/components to their shapes.

	:param items:
	:param selection_if_empty: True by default. If true, and no items is provided, current selection is used.
	:param convert: True bu default. When True, the selection is converted to shapes.
			When False, the current selection is only filtered to shapes.
	:return: List of strings with shapes' names. Empty list if nothing selected.
	"""
	if convert:
		items = default_input.items_list_in_scene(items)
		items += to_children(items, False, fullPath=True)
		items = to_full_paths_unique(items, False)
	list_f = default_input.selection_if_empty_f(selection_if_empty)
	return list_f(items, objectsOnly=1, shapes=1)


def to_transforms(items=None, selection_if_empty=True, fullPath=False):
	"""
	Converts given list of objects/components to their transforms.
	It does so by first converting items to shapes and then searching these shapes' transforms.
	:param items:
	:param selection_if_empty: True by default. If true, and no items is provided, current selection is used.
	:param fullPath: The result may be forced to have full path on each element.
	:param ls_args: Arguments for Maya's ls command which is performed during conversion to shapes.
	:return: List of strings with transforms' names. Empty list if nothing selected.
	"""
	items = to_shapes(items, selection_if_empty=selection_if_empty)
	return to_parents(items, selection_if_empty=False, fullPath=fullPath)


def to_parents(items=None, selection_if_empty=True, fullPath=False, **lsRel_args):
	"""
	Converts given list of objects/components to their parents.
	:param items:
	:param selection_if_empty: True by default. If true, and no items is provided, current selection is used.
	:param fullPath: The result may be forced to have full path on each element.
	:param lsRel_args: Additional arguments may be passed to Maya's listRelatives function.
	:return: List of strings with parents' names. Empty list if nothing selected.
	"""
	list_f = default_input.selection_if_empty_f(selection_if_empty)
	items = list_f(items)
	kwargs = listRel_args(dict(parent=True), fullPath=fullPath, **lsRel_args)
	items = cmds.listRelatives(items, **kwargs)
	return default_input.items_list(items)


def to_children(items=None, selection_if_empty=True, immediate_only=True, fullPath=False, **lsRel_args):
	"""
	Converts given list of objects/components to their hierarchy.
	:param items:
	:param selection_if_empty: True by default. If true, and no items is provided, current selection is used.
	:param immediate_only: True by default. If true, returns only immediate hierarchy.
		Otherwise, returns also all grand-hierarchy, grand-grand hierarchy etc.
	:param fullPath: The result may be forced to have full path on each element.
	:param lsRel_args: Additional arguments may be passed to Maya's listRelatives function.
	:return: List of strings with parents' names. Empty list if nothing selected.
	"""
	list_f = default_input.selection_if_empty_f(selection_if_empty)
	items = list_f(items)
	if immediate_only:
		kwargs = dict(children=True)
	else:
		kwargs = dict(allDescendents=True)
	kwargs = listRel_args(kwargs, fullPath=fullPath, **lsRel_args)
	items = cmds.listRelatives(items, **kwargs)
	return default_input.items_list(items)


def to_names(items=None, selection_if_empty=True, **ls_args):
	list_f = default_input.selection_if_empty_f(selection_if_empty)
	items = list_f(items, **ls_args)
	items = [x.strip('|').split('|')[-1] for x in items]
	return items


def to_full_paths(items=None, selection_if_empty=True, **ls_args):
	"""
	Converts item names to full paths.
	:param selection_if_empty: True by default. If true, and no items is provided, current selection is used.
	:return: List of strings with items' full paths. Empty list if nothing selected.
	"""
	list_f = default_input.selection_if_empty_f(selection_if_empty)
	return list_f(items, long=True, **ls_args)


def to_full_paths_unique(items=None, selection_if_empty=True, **ls_args):
	"""
	First, converts item names to full paths. Second, makes sure each item is listed only once, keeping the order.
	:param selection_if_empty: True by default. If true, and no items is provided, current selection is used.
	:return: List of strings with items' full paths without duplicates. Empty list if nothing selected.
	"""
	from drl_common.utils import remove_duplicates
	items = to_full_paths(items, selection_if_empty=selection_if_empty, **ls_args)
	return remove_duplicates(items)


def to_poly_hierarchy(items=None, selection_if_empty=True):
	"""
	Converts items to the entire polygonal hierarchy, wirh all polygonal hierarchy, grand-hierarchy etc
	:param selection_if_empty: True by default. If true, and no items is provided, current selection is used.
	:return: List of strings with polygonal transforms' full paths without duplicates. Empty list if nothing selected.
	"""
	no_sel = dict(selection_if_empty=False) # to make code a little more readable
	# first, we need to query all child shapes:
	objs = to_children(items, selection_if_empty=selection_if_empty, immediate_only=False, fullPath=True)
	objs = to_shapes(objs, **no_sel)
	objs = to_full_paths_unique(objs, **no_sel)
	# and make sure they all are polygonal:
	objs = cmds.ls(objs, type='mesh')
	# Finally, query their corresponding transforms:
	objs = to_parents(objs, fullPath=True, **no_sel)
	objs = to_full_paths_unique(objs, **no_sel)
	return objs


def to_child_non_shapes(items=None, selection_if_empty=True, **ls_args):
	"""
	Queries a list of child non-shape objects.
	WARNING! ls_args acts exactly opposite then in the rest of functions here.
		Provided arguments are applied to excluded shapes and not to the actual result.
		So, if you specify type='mesh' extra argument, everything BUT child poly shapes will be listed.
		That means, any nurbs/subdiv shapes will also be in the result.
	:param selection_if_empty: True by default. If true, and no items is provided, current selection is used.
	:param ls_args: arguments for Maya's ls function applied to EXCLUDED CHILDREN.
	:return: List of strings with non-shape objects, full paths without duplicates. Empty list if nothing selected.
	"""
	from drl_common.utils import list_difference
	no_sel = dict(selection_if_empty=False) # to make code a little more readable
	children = to_children(items, selection_if_empty=selection_if_empty, fullPath=True)
	children = to_full_paths_unique(children, **no_sel)
	shapes = to_shapes(children, **no_sel)
	shapes = default_input.items_list_in_scene(shapes, **ls_args)
	shapes = to_full_paths_unique(shapes, **no_sel)
	children = list_difference(children, shapes)
	return children