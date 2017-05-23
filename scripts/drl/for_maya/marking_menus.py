__author__ = 'DRL'

from maya import cmds


def remove(menu=''):
	if menu and cmds.popupMenu(menu, exists=1):
		cmds.deleteUI(menu)


def remove_temp(right_now=False):
	menus=['tempMM', 'tempMM2']
	if right_now:
		map(remove, menus)
	else:
		map(lambda x: cmds.evalDeferred(lambda *a: remove(x), lowestPriority=1), menus)