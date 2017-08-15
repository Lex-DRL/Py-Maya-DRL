__author__ = 'DRL'

from pymel import core as pm
from drl.for_maya.ls import pymel as ls
from drl.for_maya.geo.components import uv_sets
from drl_common import errors as err

from drl.for_maya import py_node_types as _pnt
_t_transform = _pnt.transform
_t_shape_poly = _pnt.shape.poly
_tt_poly_geo = (_pnt.transform, _pnt.shape.poly)


__linkAttr_name = 'uvlSourceMeshTransform'
__linkAttr_shortName = 'uvlSrcMesh'
__linkAttr_title = 'Source Mesh (Transform)'

__uvAttr_name = 'uvlSourceUvSet'
__uvAttr_shortName = 'uvlSrcUV'
__uvAttr_title = 'Source UV-set'

__group_container_name = 'To_UV_Layout'


def __error_check_single_obj(obj, obj_name='Temp duplicate'):
	"""
	Makes sure the given obj is a transform.

	:param obj: scene object (string/PyNode: shape, transform).
	:param obj_name: How to call this object if error is thrown.
	:return: Transform node of the given object. Returned directly, not as list with single item.
	"""
	obj = ls.default_input.handle_input(obj, False)
	if not obj:
		raise ValueError(obj_name + ' not specified.')
	obj = obj[0]

	if isinstance(obj, pm.nt.Mesh):
		obj = ls.to_parent(obj, False)[0]

	err.WrongTypeError(obj, _t_transform, obj_name).raise_if_needed()
	assert isinstance(obj, _t_transform)
	return obj


def __src_mesh_attr(obj):
	"""
	Returns the attribute for linking duplicate to the source object.
	Creates it if necessary.

	:param obj: pm.nt.Transform
	:return: pm.Attribute
	"""
	assert isinstance(obj, _t_transform)
	if not obj.hasAttr(__linkAttr_name):
		pm.addAttr(
			obj,
			ln=__linkAttr_name, sn=__linkAttr_shortName, nn=__linkAttr_title,
			at='message'
		)

	a = obj.attr(__linkAttr_name)
	assert isinstance(a, pm.Attribute)
	return a


def __src_uv_attr(obj):
	"""
	Returns the attribute storing the source UV-set name.
	Creates it if necessary.

	:param obj: pm.nt.Transform
	:return: string
	"""
	assert isinstance(obj, _t_transform)
	if not obj.hasAttr(__uvAttr_name):
		pm.addAttr(
			obj,
			ln=__uvAttr_name, sn=__uvAttr_shortName, nn=__uvAttr_title,
			dt='string'
		)

	a = obj.attr(__uvAttr_name)
	assert isinstance(a, pm.Attribute)
	return a


def get_source_object(obj):
	"""
	Returns the source object of the current temporary duplicate.

	:param obj: the temporary duplicate to get the source for.
	:return: (nt.Transform) the source object this duplicate is copied from.
	"""
	obj = __error_check_single_obj(obj)
	return __src_mesh_attr(obj).get()


def set_source_object(dup_obj, src_obj, uv_set_name=''):
	"""
	Remembers in the duplicate object's transform node, which source object it's copied from.
	This should be done after the cleanup, since it (cleanup) removes all the connections.

	:param dup_obj: the duplicated temp object to store the link for
	:param src_obj: the source object
	:param uv_set_name: (optional, string) the source object's UV set
	"""
	dup = __error_check_single_obj(dup_obj)
	src = __error_check_single_obj(src_obj, 'Source object')
	src.message >> __src_mesh_attr(dup)

	if not uv_set_name:
		uv_set_name = uv_sets.get_set_name(src)
	elif not (uv_set_name in uv_sets.get_all_sets(src)):
		raise uv_sets.NoSuchUVSetError(src, uv_set_name)
	__src_uv_attr(dup).set(uv_set_name)


def get_source_uv_set(obj):
	"""
	Returns the source UV-set of the current temporary duplicate.

	:param obj: the temporary duplicate to get the source for.
	:return: (string) the name of the UV-set in source object this duplicate is copied from.
	"""
	obj = __error_check_single_obj(obj)
	return __src_uv_attr(obj).get()


def set_source_uv_set(dup_obj, uv_set_name=''):
	"""
	Remembers in the duplicate object's transform node, which UV-set it's copied from.

	:param dup_obj: the duplicated temp object
	:param uv_set_name: (optional, string) the source object's UV set
	"""
	dup = __error_check_single_obj(dup_obj)
	__src_uv_attr(dup).set(uv_set_name)


def __get_group_container():
	"""
	Returns a group container transform. Creates it if necessary.
	:return: nt.Transform
	"""
	clashes = pm.ls(__group_container_name)
	for c in clashes:
		# if it's not a transform or it is and it's parented to something,
		# then we need to rename it
		if (
			ls.short_item_name(c) == __group_container_name
			and not pm.ls(c, tr=1)
			or ls.to_parent(c, False)
		):
			pm.rename(c, __group_container_name + '1')

	full_name = '|' + __group_container_name
	if pm.objExists(full_name):
		return pm.PyNode(full_name)

	return pm.group(n=__group_container_name, world=True, empty=True)


def __prepare_single_duplicate(src_obj, uv_set=''):
	"""
	Prepare a duplicate of a single source object. Assuming the input is correct.

	:param src_obj: source Transform/Shape to make duplicate for
	:return: the created duplicate
	"""
	src_obj = __error_check_single_obj(src_obj, 'Source object')
	pm.delete(src_obj, ch=1)

	if (
		bool(uv_set)
		and uv_set != uv_sets.get_current(src_obj)
		and (uv_set in uv_sets.get_all_sets(src_obj))
	):
		uv_sets.set_current_for_singe_obj(src_obj, uv_set)

	dup = pm.duplicate(src_obj, rr=1)
	dup = __error_check_single_obj(dup)

	# rename and reparent to a container group:
	parent = ls.to_parent(dup, False)
	container = __get_group_container()
	if not(parent and parent[0] == container):
		pm.parent(dup, container)
	pm.rename(dup, 'toUVL_' + ls.short_item_name(src_obj))
	pm.delete(dup, ch=1)

	# remove all extra shapes:
	dup_extra_shapes = pm.listRelatives(dup, s=1)
	if not dup_extra_shapes:
		raise RuntimeError("Duplicate %s doesn't have any shapes." % dup)
	assert isinstance(dup_extra_shapes, (list, tuple))
	dup_shape = dup_extra_shapes.pop(0)
	if dup_extra_shapes:
		pm.delete(dup_extra_shapes)
	err.WrongTypeError(dup_shape, pm.nt.Mesh, 'duplicate shape').raise_if_needed()
	assert isinstance(dup_shape, pm.nt.Mesh)

	# also remove any hierarchy:
	extra_children = [x for x in pm.listRelatives(dup, children=1) if x != dup_shape]
	if extra_children:
		pm.delete(extra_children)

	# copy current UV-set to the main one
	src_set = uv_sets.get_current(dup)
	if src_set != uv_sets.get_set_name(dup, 1):
		uv_sets.copy_to_set(dup, to_set=1, from_set=src_set, selection_if_none=False)
		uv_sets.set_current_for_singe_obj(dup, 1)
	pm.delete(dup, ch=1)

	# keep only main set:
	uv_sets.keep_only_main_set(dup, selection_if_none=False)
	pm.delete(dup, ch=1)

	# remove all extra connections
	for o in [dup, dup_shape]:
		outs = o.connections(connections=1, plugs=1, destination=1, source=0)
		ins = o.connections(connections=1, plugs=1, destination=0, source=1)
		connections = outs + [(x[1], x[0]) for x in ins]
		for c in connections:
			c[0] // c[1]

	# assign default material
	pm.sets('initialShadingGroup', e=1, forceElement=dup)

	set_source_object(dup, src_obj)

	return dup


def prepare_duplicates(objects=None, selection_if_none=True):
	"""
	Generates temporary (intermediate) duplicates ready to be sent to UV Layout.
	These duplicates are cleaned-up versions of source objects,
	preventing errors which may otherwise appear when sending mesh back from UVL to Maya.

	They also contain links to the source objects and their corresponding UV-sets
	for further transferring UVs back.

	:param objects: objects in scene to generate duplicates for.
	:param selection_if_none: whether to use selection when no objects given
	:return: list of duplicates generated (they are also got selected)
	"""
	from maya import mel

	objects = ls.default_input.handle_input(objects, selection_if_none)
	for o in objects:
		err.WrongTypeError(
			o, _tt_poly_geo, 'source item'
		).raise_if_needed()
	duplicates = [__prepare_single_duplicate(src) for src in objects]
	pm.select(duplicates, r=1)

	# finally, open default UV Layout sending window
	mel.eval('uvlayout_open;')

	return duplicates


def __get_shape(obj):
	"""
	Returns the object's mesh shape no matter whether object's transform or shape is given.
	:param obj: either nt.Transform or nt.Mesh
	:return: nt.Mesh
	"""
	err.WrongTypeError(obj, _tt_poly_geo, 'object').raise_if_needed()
	if isinstance(obj, _t_shape_poly):
		return obj
	if isinstance(obj, _t_transform):
		return __get_shape(obj.getShape())


def __transfer_from_single_duplicate(dup):
	"""
	Sending UVs back from duplicate object to it's source.
	Works only with single object, assuming input is correct.

	:param dup: a duplicate's Transform/Shape node
	:return: (nt.Transform) source object that got new UVs
	"""
	dup = __error_check_single_obj(dup)
	pm.delete(dup, ch=1)

	src_obj = get_source_object(dup)
	src_set = get_source_uv_set(dup)
	pm.delete(src_obj, ch=1)

	if src_set and (uv_sets.get_current(src_obj) != src_set):
		uv_sets.set_current_for_singe_obj(src_obj, src_set)

	src_set = uv_sets.get_current(src_obj)

	pm.transferAttributes(
		__get_shape(dup), __get_shape(src_obj),
		transferPositions=0,
		transferNormals=0,
		transferUVs=1,
		sourceUvSet="map1",
		sourceUvSpace="map1",
		targetUvSet=src_set,
		targetUvSpace=src_set,
		transferColors=0,
		sampleSpace=4,
		searchMethod=0,
		flipUVs=0,
		colorBorders=1
	)

	pm.delete(src_obj, ch=1)
	return src_obj


def transfer_from_duplicates(objects=None):
	"""
	Sends updated UVs back from duplicates to their corresponding source objects,
	to their corresponding UV sets.

	:param objects: optional list of duplicates to transfer from. If none given, all the ovjects in the default container group are taken.
	:return: (list of nt.Transform) source objects. The current selection is kept intact.
	"""
	prev_sel = pm.ls(sl=1)

	objects = ls.default_input.handle_input(objects, False)
	if not objects:
		container = __get_group_container()
		objects = pm.listRelatives(container, children=1)

	objects = [__error_check_single_obj(x) for x in objects]
	if not objects:
		raise RuntimeError('No temporary duplicates given to transfer their UVs.')

	sources = [__transfer_from_single_duplicate(d) for d in objects]
	pm.select(prev_sel, r=1)

	return sources


def delete_temp_duplicates():
	"""
	This function needs to be called after all the UV layout work done,
	and you want to clean the scene from temporary objects.
	During this process, all the existing duplicates transfer their UVs to sources for the last time.

	Finally, source objects are selected.

	:return: (list of nt.Transform) source objects that were updated and selected.
	"""
	def _prepare_src(dup):
		src_obj = get_source_object(dup)
		src_set = get_source_uv_set(dup)
		pm.delete(src_obj, ch=1)
		if src_set and (uv_sets.get_current(src_obj) != src_set):
			uv_sets.set_current_for_singe_obj(src_obj, src_set)
		return src_obj

	container = __get_group_container()
	if not container:
		raise RuntimeError('Group for temporary duplicates is not found.')

	duplicates = pm.listRelatives(container, children=1)
	duplicates = [__error_check_single_obj(d) for d in duplicates]

	if not duplicates:
		return []

	transfer_from_duplicates(duplicates)
	sources = [_prepare_src(d) for d in duplicates]

	pm.delete(container)
	pm.select(sources, r=1)
	return sources