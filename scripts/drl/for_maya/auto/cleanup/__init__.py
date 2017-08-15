__author__ = 'DRL'

import os
import sys as __sys
from pymel import core as pm

from drl.for_maya.ls import pymel as ls

from . import history, materials
from .__uv_sets import UVSets, UVSetsRule
from .__uvs import UVs

_this = __sys.modules[__name__]
_str_types = (str, unicode)


# -----------------------------------------------------------------------------


def rename_pasted():
	"""
	Remove "pasted__" prefix for all the nodes in the scene.

	:return: <list of PyNode> Renamed nodes.
	"""
	return [
		pm.rename(x, x.name().replace('pasted__', '')) for x in pm.ls('pasted__*')
	]


def del_isolate_sets():
	"""
	Remove TextureEditor-isolateSets.

	:return: <list of strings> Removed nodes' names.
	"""
	res = pm.ls('*textureEditorIsolateSelectSet*', type='objectSet')
	if not res:
		return []

	res_pm = res[:]
	res = [x.name() for x in res]
	pm.delete(res_pm)
	return res


def del_all_object_sets(exclude_default_maya_sets=True):
	"""
	Remove all sets created in the scene.

	:return: <list of strings> Removed sets' names.
	"""
	all_sets = ls.all_object_sets(exclude_default_maya_sets)
	res = [x.name() for x in all_sets]
	if all_sets:
		pm.delete(all_sets)
	return res


def del_unused_nodes():
	"""
	Delete unused rendering nodes. The equivalent to selecting "Edit > Delete Unused Nodes" from Hypershade.

	Just a call to the pm.mel.MLdeleteUnused()
		* ML stands for MultiLister, the old shading interface
	"""
	pm.mel.MLdeleteUnused()


def __all_poly_shapes():
	return pm.ls(type='mesh')


def make_all_double_sided():
	"""
	Make all geometry objects in the scene double-sided.

	:return: <list of PyNode> Nodes which attribute has been changed to True.
	"""
	res = list()
	for s in __all_poly_shapes():
		a = s.doubleSided
		assert isinstance(a, pm.Attribute)
		if not a.get():
			s.doubleSided.set(True)
			res.append(s)
	return res


def rename_all_shapes():
	"""
	Make all the shape nodes' names match their transform parent, with regular "Shape" postfix.

	:return: <list of PyNode> Renamed shapes.
	"""
	res = list()
	for s in ls.all_shapes():
		p = ls.to_parent(s, False)[0]
		nn = ls.short_item_name(p) + 'Shape'
		if ls.short_item_name(s) != nn:
			pm.rename(s, nn)
			res.append(s)
	return res


def create_debug_normals_layer_if_needed(
	set_current_if_created=True,
	layer_name='testNormals',
	cgfx_plugin='cgfxShader',
	cgfx_shader=r'Y:/Farm/debug.cgfx'
):
	"""
	If not present already, this function creates debug layer
	allowing to easily check whether mesh normals face the right direction.

	:param layer_name: string, the name of the debug layer (the actual layer will get '_rl' postfix). Default: 'testNormals'
	:return: tuple: (
		0: Layer's PyNode
		1: bool: True if this layer was created, False if it was already present in the scene.
	)
	"""
	from drl_common import errors as err
	err.NotStringError(layer_name, 'layer_name').raise_if_needed()
	err.NotStringError(cgfx_plugin, 'cgfx_plugin').raise_if_needed()
	err.NotStringError(cgfx_shader, 'cgfx_shader').raise_if_needed()

	mat_name = layer_name + '_mat'
	sg_name = layer_name + '_sg'
	layer_name += '_rl'

	def error_checks():
		# if not pm.pluginInfo(cgfx_plugin, q=1, registered=1):
		# 	raise Exception('No <%s> plugin found. Cannot create debug-layer.' % cgfx_plugin)
		if not (os.path.exists(cgfx_shader) and os.path.isfile(cgfx_shader)):
			raise Exception('Shader not found. Debug-layer creation aborted.')
		if not pm.pluginInfo(cgfx_plugin, q=1, loaded=1):
			pm.loadPlugin(cgfx_plugin)

	def get_cgfx_mat():
		if ls.object_set_exists(mat_name, node_type='cgfxShader'):
			node = pm.PyNode(mat_name)
		else:
			node = pm.shadingNode('cgfxShader', asShader=1, name=mat_name)
			sg = pm.sets(renderable=1, noSurfaceShader=1, empty=1, name=sg_name)
			node.outColor.connect(sg.surfaceShader)  # node.outColor >> sg.surfaceShader
		assert isinstance(node, pm.nodetypes.CgfxShader)
		return node

	def set_cgfx_values(node):
		from drl.for_maya import plugins
		plugins.Plugin("cgfxShader").load(quiet=True)
		if not pm.cgfxShader(node, q=1, fx=1):
			pm.cgfxShader(node, e=1, fx=cgfx_shader)
		node.technique.set('SimpleWithFresnel')

	if ls.object_set_exists(layer_name, node_type='renderLayer'):
		return pm.PyNode(layer_name), False

	error_checks()

	root_objects = pm.ls('|*', tr=1)
	rl = pm.createRenderLayer(root_objects, name=layer_name, number=1, noRecurse=1)
	assert isinstance(rl, pm.nodetypes.RenderLayer)

	mat = get_cgfx_mat()
	set_cgfx_values(mat)
	pm.defaultNavigation(ce=1, source=mat, destination=rl.shadingGroupOverride)

	if set_current_if_created:
		rl.setCurrent()

	return rl, True


def cleanup_all(
	double_sided=True,
	rename_shapes=True,
	uv_sets_rename_first=True,
	uv_sets_remove_extra=True, uv_sets_kept=None,
	pasted=True, isolate_sets=True,
	debug_normals=True, switch_to_debug_lr=True
):
	from pprint import pprint as pp
	res = list()
	if isolate_sets:
		res_n = del_isolate_sets()
		if res_n:
			print '\nDeleted <isolateSelect> sets:'
			pp(res_n)
	if pasted:
		res_n = rename_pasted()
		res += res_n
		if res_n:
			print '\nRenamed "pasted" nodes:'
			pp(res_n)
	if double_sided:
		res_n = make_all_double_sided()
		res += res_n
		if res_n:
			print '\nSet Double-sided attribute for:'
			pp(res_n)
	if rename_shapes:
		res_n = rename_all_shapes()
		res += res_n
		if res_n:
			print '\nRenamed shapes:'
			pp(res_n)

	if uv_sets_rename_first or uv_sets_remove_extra:
		all_shapes = __all_poly_shapes()
		cleaner = UVSets(all_shapes, False, kept_sets_rule=uv_sets_kept)

		if uv_sets_rename_first:
			res_n = cleaner.rename_first_set()
			if res_n:
				res += res_n
				print '\nFirst UV-set renamed to "map1" for:'
				pp(res_n)
		if uv_sets_remove_extra:
			res_n = cleaner.remove_extra_sets()
			if res_n:
				res += [x[0] for x in res_n]
				print '\nRemoved extra UV-sets:'
				pp(res_n)

	if debug_normals:
		rl, created = create_debug_normals_layer_if_needed(switch_to_debug_lr)
		if created:
			print '\nCreated <debug layer> for testing normals:\n' + str(rl)

	if res:
		pm.select(res, r=True)
	else:
		pm.select(cl=True)
		print 'No problems detected. The meshes are ready to bake!'