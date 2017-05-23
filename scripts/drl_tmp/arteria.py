__author__ = 'DRL'

import maya.cmds as cmds
import maya.mel as mel
import re
from os import path
import glob as glb
import pprint as pp

sl = cmds.ls(sl=True, fl=True)
wrn = ()

for n in sl:
	# n = node
	# n = 'APRONlegs_mat'
	fl = re.match('(.*)_mat$', n).group(1)
	fldr = re.match('([A-Z_0-9]+)', fl).group(1)
	proj = cmds.workspace(q=True, fullName=True)
	# proj = 'E:/1-Projects/Maya/y-Dragoncide'
	rel_pth = 'SourceImages/Textures/Characters/0-src/' + fldr
	abs_pth = '/'.join([proj, rel_pth])
	if path.isdir( abs_pth ):
		rel_pth = '/'.join([rel_pth, fl])
		abs_pth = '/'.join([proj, rel_pth])
		found_fls = glb.glob( abs_pth + '.*' )
		if len(found_fls):
			rel_pth += found_fls[0][-4:]
			cmd_create = \
				'createRenderNodeCB -as2DTexture "" file "defaultNavigation -force true -connectToExisting ' +\
				'-source %node -destination ' + n + '.color; ' +\
				'window -e -vis false createRenderNodeWindow;";'
			fl_nd = mel.eval(cmd_create)
			cmds.setAttr( fl_nd + '.fileTextureName', rel_pth, type='string' )
		else:
			wrn += ( '/'.join([fldr, fl]), )
	else:
		wrn += (fldr,)

pp.pprint(wrn)