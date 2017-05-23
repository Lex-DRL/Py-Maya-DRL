__author__ = 'DRL'

import warnings as wrn

from maya import cmds

def items_input(items=None, stacklevel_offset=0):
	"""
	Performs basic error-check for the input list of objects/components.
	When nothing is given, current selection is used.

	:param items: the input which may contain wrong objects/components (caused by human error).
	:param stacklevel_offset: used to define the level of warnings.
	:return:
	"""
	if isinstance(items, type(None)):
		msg = '\nEmpty list of items is given.\nContinuing with current selection.'
		wrn.warn(msg, RuntimeWarning, stacklevel=2+stacklevel_offset)
		items = cmds.ls(sl=1)
	elif isinstance(items, (set, tuple)):
		msg = '\n<items> argument is set or tuple.\nConverting it to list to avoid further troubles.'
		wrn.warn(msg, RuntimeWarning, stacklevel=2+stacklevel_offset)
		items = list(items)
	elif not(isinstance(items, (list, str, unicode))):
		msg = '\nWrong data type for <items> argument.\nReturning nothing.'
		wrn.warn(msg, RuntimeWarning, stacklevel=2+stacklevel_offset)
		return None

	items = cmds.ls(items)  # make sure these items exist
	if not items:
		msg = '\nEmpty list is given.\nReturning nothing.'
		wrn.warn(msg, RuntimeWarning, stacklevel=2+stacklevel_offset)
		return None

	return items