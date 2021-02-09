__author__ = 'Lex Darlog (DRL)'

from drl_common import errors as _err

from drl.for_maya import py_node_types as _pnt
_t_transform = _pnt.transform
_t_shape_geo = _pnt.shape.geo
_t_obj_poly = (_t_transform, _pnt.shape.poly)

# transform, poly shape and all the poly component types
_tt_poly_geo_all = tuple(
	[_t_transform, _pnt.shape.poly] +
	list(_pnt.comp.poly.any_tuple)
)


class ItemsProcessorBase(object):
	"""
	A base class, that provides the <items> property (elements to process via child class)
	and handles setting it appropriately.
	I.e.:

		* Items are checked via default_input.handle_input()
		* They can be filtered to only specific types (see below).

	:param allowed_py_node_types:
		When a type or a tuple of types specified, this will act as a filter,
		passing only those items that match the given type.

		Anything else won't go to the <items> list.
	:param hierarchy:
		Specifies whether to process children, grandchildren etc. It doesn't change
		the actual <items> list. However, the methods will work with respect to that.
	:type hierarchy: bool
	"""
	def __init__(self, allowed_py_node_types=None, hierarchy=False):
		super(ItemsProcessorBase, self).__init__()
		self.__items = list()
		self.__py_node_types_allowed = None
		self.__set_items = self.__set_items_unfiltered
		if not(allowed_py_node_types is None):
			self.__set_filtering_types(allowed_py_node_types)
			self.__set_items = self.__set_items_filtered_by_py_node_type
		self.hierarchy = bool(hierarchy)

	def __set_filtering_types(self, types):
		self.__py_node_types_allowed = _err.NotTypeError(types, 'types').raise_if_wrong_arg_for_isinstance()

	def __set_items_unfiltered(self, items=None, selection_if_none=True):
		"""
		Called only if filtering types not provided.
		"""
		from drl.for_maya.ls.pymel import default_input as _def
		# preventing recursive import ^

		items = _def.handle_input(items, selection_if_none)
		if not items:
			self.__items = list()
			return
		self.__items = items

	def __set_items_filtered_by_py_node_type(self, items=None, selection_if_none=True):
		"""
		Called only if filtering types are specified via <allowed_py_node_types> argument.
		"""
		from drl.for_maya.ls.pymel import default_input as _def
		# preventing recursive import ^

		items = [
			x for x in _def.handle_input(items, selection_if_none)
			if isinstance(x, self.__py_node_types_allowed)
		]
		if not items:
			self.__items = list()
			return
		self.__items = items

	def set_items(self, items=None, selection_if_none=True):
		"""
		Setter for <items>, which also returns self.

		:param items: nodes/components
		:param selection_if_none: whether to use selection if <items> is None
		:return: self
		"""
		self.__set_items(items, selection_if_none)
		return self

	@property
	def items(self):
		return self.__items[:]

	@items.setter
	def items(self, value):
		self.set_items(value, selection_if_none=False)

	def get_geo_items(self):
		"""
		Returns the list of geometry items, ready to be processed.
		I.e., all the transforms in the <items> list are converted to their shapes.
		All the non-transform items are passed through intact.

		If <allowed_py_node_types> was provided, the found shapes are filtered with this.

		The actual <items> list is intact. Only the returned list is generated.

		:rtype: list[_pnt.PyNode]
		"""
		from drl.for_maya.ls import pymel as _ls
		# we can't import it ^ in the top of the module, it will cause recursive import
		# so we have to do it personally for this method, here.

		allowed_types = self.__py_node_types_allowed

		def _to_direct_shapes(transform):
			# list shapes immediately after this transform
			dir_shapes = _ls.to_children(
				transform, False,
				keep_shapes=1, keep_source_objects=0,
				remove_duplicates=1  # in case of instances
			)
			return filter(
				lambda x: isinstance(x, _t_shape_geo),
				dir_shapes
			)

		def _to_hierarchy_shapes(transform):
			# list entire hierarchy of shapes
			hr_shapes = _ls.to_hierarchy(
				transform, False,
				keep_shapes=1, keep_source_objects=0,
				remove_duplicates=1  # in case of instances
			)
			return filter(
				lambda x: isinstance(x, _t_shape_geo),
				hr_shapes
			)

		def _filter_with_allowed_types(shapes):
			# keep only allowed types (call it only if types are specified)
			return filter(
				lambda x: isinstance(x, allowed_types),
				shapes
			)

		# generate the actual function that will return the list of appropriate child shapes:
		to_shapes_f = _to_hierarchy_shapes if self.hierarchy else _to_direct_shapes
		filtered_shapes_f = to_shapes_f
		if not(allowed_types is None):
			filtered_shapes_f = lambda x: _filter_with_allowed_types(to_shapes_f(x))

		res = list()
		res_append = res.append
		res_extend = res.extend

		def _add_single(item):
			if not isinstance(item, _t_transform):
				res_append(item)
				return
			# now we're sure it's transform
			res_extend(
				filtered_shapes_f(item)
			)

		# process all the items:
		map(_add_single, self.__items)
		return res


class PolyObjectsProcessorBase(ItemsProcessorBase):
	def __init__(self, items=None, selection_if_none=True, hierarchy=False):
		super(PolyObjectsProcessorBase, self).__init__(
			_t_obj_poly,
			hierarchy=hierarchy
		)
		self.set_items(items, selection_if_none)


class PolyItemsProcessorBase(ItemsProcessorBase):
	"""
	Poly geometry processor class.
	It overrides the constructor, specifying the allowed PyNode types for the input,
	so only poly items will be processed.

	:param hierarchy:
		During any PolyConversions, how to convert transforms with children:
			* True - each Transform is converted to the components of the entire hierarchy.
			* False - only the "direct" children's components are in the result.
		It affects only transforms in the items list.
	:type hierarchy: bool
	"""
	def __init__(self, items=None, selection_if_none=True, hierarchy=False):
		super(PolyItemsProcessorBase, self).__init__(
			_tt_poly_geo_all,
			hierarchy=hierarchy
		)
		self.set_items(items, selection_if_none)
