__author__ = 'Lex Darlog (DRL)'


import pymel.core as _pm
from pymel.core import PyNode

from . import default_input as _def

from drl_common import (
	errors as _err,
	utils as _utils,
)
from drl_common.py_2_3 import (
	str_t as _str_t,
	str_h as _str_h,
)

from drl.for_maya import py_node_types as _pnt
_t_sg = _pnt.sg
_t_shape = _pnt.shape
_t_transform = _pnt.transform
_t_shape_any = _pnt.shape.any
_t_comp_any = _pnt.comp.any
_t_PyNode_or_str = tuple([PyNode] + list(_str_t))


def all_objects(no_shapes=True, **ls_args):
	"""
	Lists all the DAG objects in the scene, possibly without their shapes.

	:rtype: list[PyNode]
	"""
	all_objs = _pm.ls(dag=True, **ls_args)
	is_shape_f = is_shape_checker_f()
	return [x for x in all_objs if not(no_shapes and is_shape_f(x))]


def to_objects_filter(items=None, selection_if_none=True, no_shapes=True):
	"""
	Filters given items list to only objects(their transforms)

	:rtype: list[PyNode]
	"""
	all_objs = all_objects(no_shapes)
	items = _def.handle_input(items, selection_if_none)
	return [x for x in _pm.ls(items, fl=True) if x in all_objs]


def to_objects(
	items=None, selection_if_none=True,
	shape_to_object=True, component_to_shape=False, remove_duplicates=False,
	include_intermediate=False
):
	"""
	Convert given items to objects.

	* Shapes are converted to their transforms.
	*
		Components are converted to either their shapes or transforms,
		depending on <component_to_shape> argument.

	:param items: Objects/components to convert.
	:param selection_if_none: whether to use selection if <items> is None
	:param shape_to_object:
		When True, the provided shapes are also turned to objects.
		They're intact otherwise.
	:param component_to_shape:
		if True, components are converted to shapes.
		Otherwise, they're turned to transforms (objects), too.
	:param remove_duplicates:
		When multiple components selected, they can cause their object to appear
		multiple times in result. To avoid it, set this argument as True.
		However, it takes some extra time, so it's False by default.

		Leave it as is if you don't care of objects order
		(and can just turn result to a set).
	:param include_intermediate:
			* When **True**, also list shapes that aren't displayed but used in history.
			*
				When **False** (default), such intermediate nodes (shapes/transforms)
				will be excluded from the result, even if they were in the source list.
	:return: Transforms or Shapes.
	:rtype: list[PyNode]
	"""
	items = _def.handle_input(items, selection_if_none)
	comp_to_node_f = (
		(lambda c: c.node()) if component_to_shape
		else lambda c: c.node().parent(0)
	)

	res = list()

	def _append_converted(o):
		node = o
		if isinstance(node, _t_comp_any):
			node = comp_to_node_f(node)
		elif shape_to_object and isinstance(node, _t_shape_any):
			node = node.parent(0)
		node = _err.WrongTypeError(
			node, (_t_transform, _t_shape_any), 'item', 'DAG object'
		).raise_if_needed()
		if node.intermediateObject.get() and not include_intermediate:
			return
		res.append(node)

	for i in items:
		_append_converted(i)

	if remove_duplicates:
		return _utils.remove_duplicates(res)

	return res


def all_object_sets(exclude_default_sets=True):
	"""
	All object sets in the scene.

	:param exclude_default_sets:
		If **True**, the default Maya sets are not included to the result.
	:return: ObjectSets
	:rtype: list[PyNode]
	"""
	all_sets = [
		x for x in _pm.ls(type='objectSet')
		if not isinstance(x, _t_sg)
	]
	if not exclude_default_sets:
		return all_sets

	default_names = (
		'defaultLightSet'.lower(),
		'defaultObjectSet'.lower()
	)

	def _is_default(name_lower):
		return any(map(
			lambda d: name_lower.startswith(d) or name_lower.endswith(d),
			default_names
		))

	return [
		s for s in all_sets
		if not _is_default(
			short_item_name(s).lower()
		)
	]




def all_shapes(include_intermediate=False):
	"""
	Returns all the shapes in the scene

	:param include_intermediate:
		Also list shapes that aren't displayed but used in history.
	:rtype: list[PyNode]
	"""
	return _pm.ls(dag=True, shapes=True, noIntermediate=not include_intermediate)


def all_parents(objects=None, selection_if_none=True, include_current_transforms=False):
	"""
	Lists all the parents of given object(s).

	:param objects: objects to list parents for
	:param selection_if_none: whether to use selection if <objects> is None
	:param include_current_transforms:
		if True, objects(not shapes) from <objects> will be added to result
	:rtype: list[PyNode]
	"""
	objects = _def.handle_input(objects, selection_if_none)
	parents = _pm.listRelatives(objects, allParents=True)
	if include_current_transforms:
		parents += [x for x in objects(objects, selection_if_none) if not x in parents]
	return parents


def to_parent(objects=None, selection_if_none=True, shape_as_object=False):
	"""
	The parent of a given objects.
	It returns only the immediate parent, not all of them.

	But since you could provide multiple objects at once, list is always returned.

	:param objects: objects to list parents for
	:type objects:
		str|unicode|PyNode|list[str|unicode|PyNode]|tuple[str|unicode|PyNode]
	:param selection_if_none: whether to use selection if <objects> is None
	:param shape_as_object:
		if True, the provided shape/component is considered as object.

		I.e., instead of returning shape's immediate transform,
		it's parent transform is returned
		(a parent transform of shape's transform).
	:rtype: list[PyNode]
	"""
	kw_args = dict(
		shape_to_object=False,
		component_to_shape=True
	)
	if shape_as_object:
		kw_args = dict(
			shape_to_object=True,
			component_to_shape=False
		)

	objects = to_objects(
		objects, selection_if_none,
		remove_duplicates=True,
		**kw_args
	)
	return _pm.listRelatives(objects, parent=True)


def to_hierarchy(
	items=None, selection_if_none=True,
	from_shape_transforms=False, keep_shapes=False, keep_source_objects=True,
	remove_duplicates=False, include_intermediate=False
):
	"""
	Converts given list of objects to their entire hierarchies.

	As a 1st step, given list is converted to objects (transforms).

	:param items: source parents.
	:type items:
		str|unicode|PyNode|list[str|unicode|PyNode]|tuple[str|unicode|PyNode]
	:param selection_if_none: whether to use selection if <items> is None
	:param from_shape_transforms:
		When true, source shapes are considered as their parent objects.
		So all the children will be returned even if you provided a shape.
	:param keep_shapes:
		Whether to keep child shapes in result, too.
		By default, only hierarchy of transforms is returned.
		It DOESN'T affect the provided input, if <keep_source_objects> is True.
	:param keep_source_objects:
		also keep the source objects themselves in the result.
	:param remove_duplicates:
		When multiple components provided as input, they can cause their object
		to appear multiple times in result (as well as their children).
		To avoid it, set this argument as True. However, it takes some extra time,
		so it's False by default.

		Leave it as is if you don't care of objects order
		(and can just turn result to a set).
	:param include_intermediate:
		Also list shapes that aren't displayed but used in history.
	:rtype: list[PyNode]
	"""
	items = to_objects(
		items, selection_if_none,
		shape_to_object=from_shape_transforms, component_to_shape=(not from_shape_transforms)
	)
	res = list()
	if keep_source_objects:
		res = items[:]

	res.extend([
		i for i in _pm.listRelatives(items, allDescendents=1, noIntermediate=not include_intermediate)
		if keep_shapes or not isinstance(i, _t_shape_any)
	])

	if remove_duplicates:
		return _utils.remove_duplicates(res)

	return res


def to_geo_nodes(
	items=None, selection_if_none=True, remove_duplicates=False,
	include_intermediate=False
):
	"""
	Converts list of given items to the actual Geo-PyNodes.
	I.e., to either shapes or transforms.

	:param items: source list
	:type items:
		str|unicode|PyNode|list[str|unicode|PyNode]|tuple[str|unicode|PyNode]
	:param selection_if_none: whether to use selection if <items> is None
	:param include_intermediate:
			* When **True**, also list shapes that aren't displayed but used in history.
			*
				When **False** (default), such intermediate nodes (shapes/transforms)
				will be excluded from the result, even if they were in the source list.
	:return: Transforms or Shapes.
	:rtype: list[PyNode]
	"""
	return to_objects(
		items, selection_if_none,
		shape_to_object=False, component_to_shape=True,
		remove_duplicates=remove_duplicates, include_intermediate=include_intermediate
	)


def to_children(
	items=None, selection_if_none=True,
	from_shape_transforms=False, keep_shapes=False, keep_source_objects=True,
	remove_duplicates=False, include_intermediate=False
):
	"""
	Converts given list of objects to their immediate children.

	As a 1st step, given list is converted to objects (transforms).

	:param items: source parents.
	:type items:
		str|unicode|PyNode|list[str|unicode|PyNode]|tuple[str|unicode|PyNode]
	:param selection_if_none: whether to use selection if <items> is None
	:param from_shape_transforms:
		When true, source shapes are considered as their parent objects.
		So that shape's siblings will be returned even if parent is not selected.
	:param keep_shapes:
		whether to keep child shapes in result, too.
		By default, only hierarchy of transforms is returned.
		It DOESN'T affect the provided input, if <keep_source_objects> is True.
	:param keep_source_objects: also keep the source objects themselves in the result.
	:param remove_duplicates:
		When multiple components provided as input, they can cause their object
		to appear multiple times in result (as well as their children).
		To avoid it, set this argument as True. However, it takes some extra time,
		so it's False by default.

		Leave it as is if you don't care of objects order
		(and can just turn result to a set).
	:param include_intermediate:
		Also list shapes that aren't displayed but used in history.
	:rtype: list[PyNode]
	"""
	items = to_objects(
		items, selection_if_none,
		shape_to_object=from_shape_transforms, component_to_shape=(not from_shape_transforms)
	)
	res = list()
	if keep_source_objects:
		res = items[:]

	res.extend([
		i for i in _pm.listRelatives(items, children=1, noIntermediate=not include_intermediate)
		if keep_shapes or not isinstance(i, _t_shape_any)
	])

	if remove_duplicates:
		return _utils.remove_duplicates(res)

	return res


def short_item_name(item):
	"""
	Returns simple string name of object/component itself (without preceding path).

	:type item: string|unicode|PyNode
	:rtype: string|unicode
	"""
	if isinstance(item, (list, tuple, set)) and len(item) == 1:
		item = [x for x in item][0]
	if isinstance(item, PyNode):
		item = _err.WrongTypeError(
			item, (_pm.nt.DependNode, _t_comp_any), 'item'
		).raise_if_needed()
		item = item.name()
	item = _err.NotStringError(item, 'item').raise_if_needed_or_empty()
	item = item.split('|')[-1]
	assert isinstance(item, _str_t)
	return item


def long_item_name(item, keep_comp=True):
	"""
	Returns simple string name of object/component itself.

	The name is long (i.e., full path).

	:type item: string|unicode|PyNode
	:param keep_comp:
		* When enabled (default), also keeps the actual component (i.e., `.vtx[0]`).
		* When False, truncates the output name to the shape this comp belongs to.
	:rtype: string|unicode
	"""
	if isinstance(item, (list, tuple, set)) and len(item) == 1:
		item = [x for x in item][0]

	if isinstance(item, _str_t):
		item = _err.NotStringError(item, 'item').raise_if_needed_or_empty()
		item = _pm.ls(item)
		if not item:
			raise _err.WrongValueError(item, 'item', 'existing Maya item (node/component)')
		item = item[0]

	item = _err.WrongTypeError(item, PyNode, 'item').raise_if_needed()

	extra = ''
	if isinstance(item, _t_comp_any):
		if keep_comp:
			extra = '.' + item.name().split('.')[-1]
		item = item.node()

	item = _err.WrongTypeError(item, _pm.nt.DependNode, 'item').raise_if_needed()
	name = item.longName() + extra
	assert isinstance(name, _str_t)
	return name


def is_shape_checker_f(
	geo_surface=False, any_geo=False, light=False, camera=False, exact_type=None
):
	"""
	This function generates a function to check whether some node is a shape.

	:param geo_surface: Whether we're checking if the node is Geo-Surface.
	:param any_geo:
		Whether we're checking if the node is any Geo-shape.

		Including Geo-Surfaces,
		but also including any other renderable geo: particles, fluids, etc.
	:param light: Whether we're checking if the node is Light-shape.
	:param camera: Whether we're checking if the node is Camera-shape.
	:param exact_type: A PyNode subclass to check for.
	:return: function, taking 1 argument and checking whether it is a shape.
	"""
	def _attach_exact_type(out_arr, checked_type):
		if not issubclass(checked_type, PyNode):
			raise _err.WrongTypeError(checked_type, var_name='exact_type', types_name='subclass of <PyNode>')
		out_arr.append(checked_type)

	nt = _t_shape_any
	is_exact = not(exact_type is None)
	if any([geo_surface, any_geo, light, camera, is_exact]):
		nt = list()
		if is_exact:
			if isinstance(exact_type, (list, tuple, set)):
				for x in exact_type:
					_attach_exact_type(nt, x)
			else:
				_attach_exact_type(nt, exact_type)
		if any_geo:
			nt.append(_t_shape.geo)
		if geo_surface:
			nt.append(_t_shape.surf)
		if light:
			nt.append(_t_shape.light)
		if camera:
			nt.append(_t_shape.camera)
		nt = tuple(nt)

	return lambda node: isinstance(node, nt)


def is_shape(
	node, geo_surface=False, any_geo=False, light=False, camera=False, exact_type=None
):
	"""
	Is the given node a shape of provided type.

	If no specific type is given, the node is checked to be a generic pm.nt.Shape.
	Otherwise, the node is checked to be any of the given types.

	:param node: checked object
	:type node: string|unicode|PyNode
	:param geo_surface: Whether we're checking if the node is Geo-shape.
	:param any_geo:
		Whether we're checking if the node is any Geo-shape.

		Including Geo-Surfaces,
		but also including any other renderable geo: particles, fluids, etc.
	:param light: Whether we're checking if the node is Light-shape.
	:param camera: Whether we're checking if the node is Camera-shape.
	:param exact_type: A PyNode subclass to check for.
	:rtype: bool
	"""
	# first, generate a function-checker with the given shape-type arguments:
	checker = is_shape_checker_f(geo_surface, any_geo, light, camera, exact_type)

	node = _def.handle_input(node, selection_if_none=False)[0]
	return checker(node)


def to_shapes(
	items=None, selection_if_none=True,
	geo_surface=False, any_geo=False, light=False, camera=False, exact_type=None,
	remove_duplicates=False, include_intermediate=False
):
	"""
	Converts the given items (nodes/components) to the shapes. I.e.:
		* If shape is given and it matches selected shape type, it's untouched.
		*
			If transform/component is given, they're converted to their shapes,
			if they match given type.

	If no flags limiting a shape type are enabled, shapes of any type are returned.

	:param items: source nodes/components
	:type items:
		str|unicode|PyNode|list[str|unicode|PyNode]|tuple[str|unicode|PyNode]
	:param selection_if_none: whether to use selection if <items> is None
	:type selection_if_none: bool
	:param geo_surface: Whether we're checking if the node is Geo-shape.
	:type geo_surface: bool
	:param any_geo:
		Whether we're checking if the node is any Geo-shape.

		Including Geo-Surfaces,
		but also including any other renderable geo: particles, fluids, etc.
	:type any_geo: bool
	:param light: Whether we're checking if the node is Light-shape.
	:type light: bool
	:param camera: Whether we're checking if the node is Camera-shape.
	:type camera: bool
	:param exact_type: A PyNode subclass to check for.
	:type exact_type: None|PyNode
	:param remove_duplicates:
		When multiple components provided as input, they can cause their shape
		to appear multiple times in result (as well as their children).
		To avoid it, set this argument as True. However, it takes some extra time,
		so it's False by default.

		Leave it as is if you don't care of objects order
		(and can just turn result to a set).
	:type remove_duplicates: bool
	:param include_intermediate:
		Also list shapes that aren't displayed but used in history.
	:type include_intermediate: bool
	:return: Shapes
	:rtype: list[PyNode]
	"""
	items = _def.handle_input(items, selection_if_none)

	# it's a function, not a variable:
	is_right_shape = is_shape_checker_f(geo_surface, any_geo, light, camera, exact_type)

	res = list()
	for o in items:
		if isinstance(o, _t_comp_any):
			o = o.node()

		if is_right_shape(o):
			if not(o in res):
				res.append(o)
		elif isinstance(o, _t_transform):
			child_shapes = _pm.listRelatives(o, shapes=True, noIntermediate=not include_intermediate)
			res += [
				c for c in child_shapes
				if is_right_shape(c) and not (c in res)
			]

	if remove_duplicates:
		return _utils.remove_duplicates(res)
	return res


def object_set_exists(set_node, node_type='objectSet'):
	"""
	Checks whether a maya set with the given name exists.

	:type set_node: string|unicode|PyNode
	:param node_type: the name of Maya's object type for set. Default: 'objectSet'
	:rtype: bool
	"""
	from maya import cmds
	_err.NotStringError(node_type, 'node_type').raise_if_needed()
	_err.WrongTypeError(
		set_node, _t_PyNode_or_str, 'set_node'
	).raise_if_needed()
	node = short_item_name(set_node)
	if _pm.objExists(node):
		for n in cmds.ls(node, long=True):
			if (
					n == node or
					n == ('|' + node)
			) and _pm.nodeType(n) == node_type:
				return True
	return False


def un_flatten_components(items=None, selection_if_none=True):
	"""
	Performs the opposite operation to the "flatten" argument
	used in many Maya's built-in listing commands.
	I.e., it combines sequences of 1D-components to a single <**_pm.Component**> item.

	If a sub-sequence of items contains components which make a range, but are listed
	in the wrong order, the range is detected anyway.
	In each range, duplicates are removed.

	:param items: nodes/components
	:type items:
		str|unicode|PyNode|list[str|unicode|PyNode]|tuple[str|unicode|PyNode]
	:param selection_if_none: whether to use selection if <items> is None
	:return:
		Un-flattened objects, with sequences of components merged into a single item.
	:rtype: list[PyNode]
	"""
	import itertools

	items = _def.handle_input(items, selection_if_none)
	if len(items) < 2:
		return items

	res = list()
	res_append = res.append
	res_extend = res.extend

	def _get_index_ranges_for_group(group_items):
		"""
		Generates a tuple of index ranges for the list of components.

		:param group_items:
			<iterable>
			List of components of the same type on the same shape
			(in any order, whether flattened or not).
		:return: <tuple of (start, end) ints> Sorted ranges of indices.
		"""
		indices = list()
		indices_extend = indices.extend
		for comp in group_items:
			indices_extend(comp.indicesIter())
		return _utils.to_ranges(
			sorted(set(indices))
		)

	def _add_to_res(key, group_generator):
		"""
		Append the given group of items to the result.

		:param key:
			Key of a group. Either False or component prefix.
			e.g.: **'pSphereShape2.f'**

			The name of a node in the prefix has to be unique
			(it is, since the key is generated with _item_id() function below)
		:param group_generator: <generator> the actual group of items
		"""
		elements = list(group_generator)
		if key is False or len(elements) < 2:
			# not a Component1D or a group of zero/single element anyway
			res_extend(elements)
			return

		# now we're guaranteed to have a list of Component1D
		# of the same type (vertex/face/etc)
		index_ranges = _get_index_ranges_for_group(elements)
		if len(index_ranges) == len(elements):
			# components of a same type on the same object, but none of them form a range
			res_extend(elements)
			return

		# we have at least a single range
		for start, end in index_ranges:
			template = '[{0}]' if start == end else '[{0}:{1}]'
			item_str = key + template.format(start, end)
			res_append(PyNode(item_str))


	def _item_id(itm):
		"""
		Generate unique group-key for an item.

		:param itm: PyNode
		:return:
			a key:
				*
					<string>
					a unique identifier for Component1D,

					something like: **'pSphereShape2.f'** (the shortest unique name is used)
				* <bool> for any other PyNode, **False**
		"""
		if not isinstance(itm, _pm.Component1D):
			return False
		return itm.name().rstrip('[0123456789]:')

	for key_group in itertools.groupby(items, _item_id):
		_add_to_res(*key_group)

	return res


def sorted_items(items=None, selection_if_none=True, remove_duplicates=True):
	"""
	:param items: nodes/components
	:type items:
		str|unicode|PyNode|list[str|unicode|PyNode]|tuple[str|unicode|PyNode]
	:param selection_if_none: whether to use selection if <items> is None
	:param remove_duplicates: when True (default), ensures each item appears only once in the result.
	:rtype: list[PyNode]
	"""
	items = _def.handle_input(items, selection_if_none)
	if not items:
		return list()
	if remove_duplicates:
		items = set(items)
	return sorted(items, key=long_item_name)
