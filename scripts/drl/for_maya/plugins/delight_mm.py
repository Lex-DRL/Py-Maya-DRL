__author__ = 'Lex Darlog (DRL)'

from maya import cmds, mel

def delight_enabled():
	import re
	loadedPlugins = sorted(cmds.pluginInfo(q=1, listPlugins=1))
	delightEnabled = False
	for p in loadedPlugins:
		if re.match(
			'3delight.+%s(x64)*' % cmds.about(file=1),
			p
		):
			delightEnabled=True
			break
	return delightEnabled

def delight_menu_version():
	'''
	Checks which major version of 3delight Maya plugin is used.
	6 = 3delight 10
	7 = 3delight 11
	:return:
	'''
	return cmds.delightAbout(pluginVersionIntArray=1)[0]


def connectBakePass_buildMenu(menuName=''):
	cmds.menu(menuName, e=1, deleteAllItems=1)

	renderPasses = cmds.ls(sl=1, type='delightRenderPass')
	if not renderPasses:
		cmds.menuItem(
			label='<Select Parent pass first>',
			annotation='First, you need to select the pass you want to link to bake pass',
			enable=0,
			parent=menuName
		)
		return

	#renderPasses = ['QQQ', 'WWW']
	parent = renderPasses[0]
	renderPasses = mel.eval('DRP_getAllRenderPasses();')
	renderPasses.remove(parent)

	if not renderPasses:
		cmds.menuItem(
			label='<No more passes created yet>',
			annotation='To connect your current pass to a bake pass, you need to create some bake pass first',
			enable=0,
			parent=menuName
		)
		return

	for child in renderPasses:
		# child = renderPasses[0]
		formatArgs = dict(parent=parent, child=child)
		cmds.menuItem(
			label=child,
			annotation='Connect "{child}" as bake pass for "{to_parent}"'.format(**formatArgs),
			command=connectBakePass(parent=parent, child=child),
			parent=menuName
		)


def connectBakePass(parent='', child='', forEachFrame=True):
	'''
	Adds some extra controls to <to_parent> which lets automatically run <child> as a pre-pass.
	<to_parent> and <child> has to be unique names of "delightRenderPass" nodes.

	:param parent: main pass (e.g., beauty render)
	:param child: pre-pass (e.g., point-cloud-generation)
	:param forEachFrame: if True, this setup will work per-frame.
		i.e. <child> pass will run once before rendering each <to_parent> frame.
		Otherwise, <child> pass will only run once for the entire sequence render.
	:return: None
	'''
	from drl_common.utils import camel_case
	# child = 'Child_rp'
	# to_parent = 'renderPass'
	childName = camel_case(child, punctuation_to_underscores=0)
	cmds.addAttr(
		parent,
		ln='render_{0}'.format(childName),
		sn='rnd_{0}'.format(childName),
		nn='Render Bake Pass - {0}'.format(child),
		at='bool',
		dv=1,
		writable=1,
		keyable=1
	)

	if forEachFrame:
		attr = 'preFrameMEL'
	else:
		attr = 'preRenderMEL'
	formatArgs = dict(attr=attr, parent=parent)
	mel.eval('AE_defaultAddRemoveAttr("{attr}", "{to_parent}", 1);'.format(**formatArgs))

	command = cmds.getAttr('{to_parent}.{attr}'.format(**formatArgs))
	command = command.strip()
	# command = ''
	if command:
		command += '\n'
	command += (
		'if ( `getAttr "{to_parent}.rnd_{childName}"` )\n'
		'\tdelightRenderMenuItemCommand "{child}";'
	).format(parent=parent, childName=childName, child=child)
	cmds.setAttr(
		'{to_parent}.{attr}'.format(**formatArgs),
		command,
		type='string'
	)
	mel.eval('AE_updateAE;')


# =============================================================================
# -----------------------------------------------------------------------------
# =============================================================================


def marking_menu():
	from ..marking_menus import remove_temp
	from ..utils import get_modifiers
	from ..shading import thumb_switch

	remove_temp(right_now=True)
	modifiers = get_modifiers()
	delightEnabled = delight_enabled()

	def build_delight_menuItems(menu1='', menu2=''):
		menuVer = delight_menu_version()

		def update_abortItem(abort_item=''):
			if not cmds.menuItem(abort_item, q=1, exists=1):
				return
			render_state = cmds.delightRenderState(q=1, rs=1)
			if render_state == 1:
				cmds.menuItem(abort_item, edit=1, label='Aborting render...', enable=False)
			else:
				cmds.menuItem(
					abort_item,
					edit=1,
					label='Abort Render',
					enable=(render_state == 2),
					command=lambda *x: cmds.delightBgRender(abort=1)
				)

		def update_createMenu(create_menu='', marking_menu=False):
			cmds.undoInfo(swf=0)
			cmds.menu(create_menu, edit=1, deleteAllItems=1)

			cmds.setParent(create_menu, menu=1)
			cmds.menuItem(
				'delightMM_CreateMenuItem',
				label='New',
				annotation='Create new default 3delight Render Pass',
				radialPosition='N',
				boldFont=1,
				command=lambda *x: mel.eval('select `DL_createRenderPassNode`;')
			)
			if not marking_menu:
				cmds.menuItem(divider=1)
			mel.eval('delightBuildRenderPassTemplatesMenuItems("%s")' % create_menu)
			cmds.undoInfo(swf=1)

		def create_nodesMenu(nodes_menu=''):
			cmds.setParent(nodes_menu, menu=1)
			if menuVer>6:
				# for 3delight 11 and above
				cmds.menuItem(
					label='Mask Set',
					annotation='Create new 3Delight Mask Set',
					radialPosition='NW',
					boldFont=1,
					command=lambda *x: mel.eval('DMS_create;')
				)
				cmds.menuItem(
					label='Environment',
					annotation='Create new 3Delight Environment Shape',
					radialPosition='NE',
					boldFont=1,
					command=lambda *x: cmds.createNode('delightEnvironment')
				)
			if cmds.delightAbout(packageDescription=1) != '3DelightForMaya':
				cmds.menuItem(
					label='RIB',
					annotation='Create new RIB archive node',
					radialPosition='E',
					command=lambda *x: mel.eval('DRA_create;')
				)
			clipPlane_item = cmds.menuItem(
				label='Clipping Plane',
				annotation='Create new clipping plane',
				radialPosition='SE',
				italicized=1,
				command=lambda *x: mel.eval('DCP_create;')
			)
			cmds.menuItem(
				label='CSG',
				annotation='Create new Constructive Solid Geometry node',
				radialPosition='W',
				command=lambda *x: mel.eval('DCSG_create;')
			)
			coordSys_item = cmds.menuItem(
				label='Coordinate System',
				annotation='Create new coordinate system',
				radialPosition='SW',
				italicized=1,
				command=lambda *x: mel.eval('DCS_create;')
			)
			if menuVer <= 6:
				cmds.menuItem(clipPlane_item, edit=1, radialPosition='NW')
				cmds.menuItem(coordSys_item, edit=1, radialPosition='NE')

		def create_materialsMenu(materials_menu=''):
			cmds.setParent(materials_menu, menu=1)
			cmds.menuItem(
				label='3Delight Material',
				annotation='Create and assign to selected a new 3Delight Material',
				radialPosition='NE',
				boldFont=1,
				command=lambda *x: mel.eval('DSH_createAndAssignShader("3DelightMaterial");')
			)
			cmds.menuItem(
				label='Glass',
				annotation='Create and assign to selected a new 3Delight Glass',
				radialPosition='SE',
				italicized=1,
				command=lambda *x: mel.eval('DSH_createAndAssignShader("3DelightGlass");')
			)
			cmds.menuItem(
				label='Skin',
				annotation='Create and assign to selected a new 3Delight Skin',
				radialPosition='N',
				command=lambda *x: mel.eval('DSH_createAndAssignShader("3DelightSkin");')
			)
			cmds.menuItem(
				label='Hair',
				annotation='Create and assign to selected a new 3Delight Hair',
				radialPosition='S',
				command=lambda *x: mel.eval('DSH_createAndAssignShader("3DelightHair");')
			)

		cmds.setParent(menu1, menu=1)

		if menuVer > 6:
			# for 3delight 11 and above
			cmds.menuItem(
				'delightMM_RenderLastMenuItem',
				label='Render',
				annotation='Render previous pass',
				radialPosition='W',
				boldFont=1,
				command=lambda *x: mel.eval('_3DelightRender();')
			)
			cmds.menuItem(
				'delightMM_RenderIPR',
				label='IPR Render',
				annotation='Launch IPR Session',
				optionBox=1,
				boldFont=1,
				command=lambda *x: mel.eval('DSH_launchIPR("");')
			)
			abort_item = cmds.menuItem(
				'delightMM_AbortRenderMenuItem',
				annotation='Abort render running in the background',
				radialPosition='NW'
			)
			update_abortItem(abort_item)
			create_menu = cmds.menuItem(
				'delightMM_CreateRenderPassMenu',
				label='Create',
				annotation='Create new 3delight Render Pass',
				subMenu=1, tearOff=0,
				radialPosition='NE',
				italicized=1
			)
			cmds.menuItem(
				create_menu,
				edit=1,
				postMenuCommand=lambda *x: update_createMenu(create_menu=create_menu, marking_menu=True)
			)
			cmds.setParent('..', menu=1)
		else:
			# for 3delight 10 and older
			cmds.menuItem(
				'delightMM_AddRenderPassMenu',
				label='Add',
				annotation='Add new 3delight Render Pass',
				subMenu=1, tearOff=0,
				radialPosition='NE',
				postMenuCommand=lambda *x: mel.eval('delightBuildAddRenderPassMenu "delightMM_AddRenderPassMenu"'),
				italicized=1
			)
			cmds.setParent('..', menu=1)

		cmds.menuItem(
			'delightMM_RenderRenderPassMenu',
			label='Render with',
			annotation='Render 3delight Pass',
			subMenu=1, tearOff=0,
			radialPosition='SW',
			postMenuCommand=lambda *x: mel.eval('delightBuildRenderPassMenu("MM_Render", "delightRenderMenuItemCommand", 1);')
		)
		cmds.setParent('..', menu=1)
		cmds.menuItem(
			'delightMM_SelectRenderPassMenu',
			label='Select',
			annotation='Select 3delight Render Pass',
			subMenu=1, tearOff=0,
			radialPosition='E',
			boldFont=1,
			postMenuCommand=lambda *x: mel.eval('delightBuildRenderPassMenu("MM_Select", "select", 1);')
		)
		cmds.setParent('..', menu=1)
		cmds.menuItem(
			'delightMM_DuplicateRenderPassMenu',
			label='Duplicate',
			annotation='Duplicate 3delight Render Pass',
			subMenu=1, tearOff=0,
			radialPosition='SE',
			postMenuCommand=lambda *x: mel.eval('delightBuildRenderPassMenu("MM_Duplicate", "duplicate -inputConnections", 0);')
		)
		cmds.setParent('..', menu=1)
		cmds.menuItem(
			'delightMM_SaveAsTemplateRenderPassMenu',
			label='Save as Template',
			annotation='Save 3delight Render Pass as Template',
			subMenu=1, tearOff=0,
			radialPosition='N',
			postMenuCommand=lambda *x: mel.eval('delightBuildRenderPassMenu("MM_SaveAsTemplate", "DRP_saveAsTemplate", 0);')
		)
		cmds.setParent('..', menu=1)
		cmds.menuItem(
			label='Relationship Editor',
			annotation='Open the 3Delight relationship editor in a floating window',
			command=lambda *x: mel.eval('DL_explorerPanel;'),
			boldFont=1
		)
		cmds.menuItem(
			label='Assignment Panel',
			annotation='Open the assignment panel in a floating window',
			command=lambda *x: mel.eval('DL_shaderAssignmentPanel;')
		)

		# -------------------------------------------------------------------------

		cmds.setParent(menu2, menu=1)
		nodes_menu = cmds.menuItem(
			'delightMM_CreateDelightNodesMenu',
			label='Create 3delight nodes',
			annotation='Create nodes provided by 3delight plug-in',
			subMenu=1, tearOff=1,
			radialPosition='N',
			boldFont=1
		)
		create_nodesMenu(nodes_menu=nodes_menu)
		cmds.setParent(menu2, menu=1)
		if menuVer > 6:
			# for 3delight 11 and above
			mats_menu = cmds.menuItem(
				'delightMM_CreateDelightMatMenu',
				label='Create Materials',
				annotation='Create and assign to selected a new 3delight materials',
				subMenu=1, tearOff=1,
				radialPosition='E',
				italicized=1
			)
			create_materialsMenu(materials_menu=mats_menu)
			cmds.setParent(menu2, menu=1)

		cmds.menuItem(
			'delightMM_DRL_linkBakePass',
			label='Link bake pass',
			annotation='Link pre-pass that will render before the selected one',
			subMenu=1, tearOff=0,
			radialPosition='W',
			postMenuCommand=lambda *x: connectBakePass_buildMenu('delightMM_DRL_linkBakePass')
		)
		cmds.setParent('..', menu=1)
		cmds.menuItem(
			label='Preferences',
			annotation='Open 3Delight for Maya Preferences',
			radialPosition='SW',
			command=lambda *x: mel.eval('DL_preferencesWindow;')
		)

	def build_warning_menuItems(menu1='', menu2=''):
		for m in [menu1, menu2]:
			cmds.setParent(m, menu=1)
			cmds.menuItem(
				label='3delight plugin is not loaded',
				annotation='You need to load the 3delight first to make the full use of this menu',
				radialPosition='N',
				enable=0,
				boldFont=1
			)
			cmds.menuItem(
				label='Plug-in Manager',
				annotation='Open Plug-in Manager to load the plugin',
				radialPosition='W',
				command=lambda *a: mel.eval('PluginManager();')
			)

	# Primary menu:
	menu1 = cmds.popupMenu(
		'tempMM',
		markingMenu=1,
		button=1,
		shiftModifier=modifiers['shift'],
		ctrlModifier=modifiers['ctrl'],
		parent='viewPanes'
	)
	# Secondary menu:
	menu2 = cmds.popupMenu(
		'tempMM2',
		markingMenu=1,
		button=2,
		shiftModifier=modifiers['shift'],
		ctrlModifier=modifiers['ctrl'],
		parent='viewPanes'
	)
	if delightEnabled:
		build_delight_menuItems(menu1=menu1, menu2=menu2)
	else:
		build_warning_menuItems(menu1=menu1, menu2=menu2)

	cmds.setParent(menu2, menu=1)
	cmds.menuItem(
		label='Connect shader attributes',
		annotation='Links all the identical attributes from the first node selected to the other ones',
		radialPosition='SE',
		command=lambda *x: mel.eval('DRL_connectIdentical;')
	)
	cmds.menuItem(
		label='Toggle thumbnail',
		annotation='Toggles thumbnail in Attribute Editor on and off',
		radialPosition='S',
		command=lambda *x: thumb_switch()
	)
	cmds.menuItem(
		label='Thumbnail ON',
		annotation='Turns thumbnail in Attribute Editor ON',
		command=lambda *x: thumb_switch(1)
	)
	cmds.menuItem(
		label='Thumbnail OFF',
		annotation='Turns thumbnail in Attribute Editor OFF',
		command=lambda *x: thumb_switch(0)
	)
