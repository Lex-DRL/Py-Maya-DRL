__author__ = 'DRL'

from maya import cmds

from drl.for_maya.geo.components.old.vertices import calc_unityCount

hudName = 'DRL_unity_vertex_count'
hudSection = 4


def command_update():
	return calc_unityCount(cmds.ls(sl=1), stacklevel_offset=1)


def build_hud():
	cmds.headsUpDisplay(
		hudName,
		s=hudSection,
		b=cmds.headsUpDisplay(nfb=hudSection),
		l=u"Unity's vertex count:",
		lfs='large',
		dfs='large',
		bs='medium',
		c=command_update,
		ev='SelectionChanged',
		nodeChanges='attributeChange'
	)
	cmds.headsUpDisplay(hudName, e=1, )


def disable():
	if cmds.headsUpDisplay(hudName, q=1, ex=1):
		cmds.headsUpDisplay(hudName, rem=1)


def enable():
	disable()
	build_hud()


def toggle():
	if cmds.headsUpDisplay(hudName, q=1, ex=1):
		cmds.headsUpDisplay(hudName, rem=1)
	else:
		build_hud()