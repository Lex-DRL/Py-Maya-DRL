__author__ = 'DRL'

from drl.for_maya.ls import pymel as _ls
_def = _ls.default_input

from drl_common import errors as _err


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
	"""
	def __init__(self, allowed_py_node_types=None):
		super(ItemsProcessorBase, self).__init__()
		self.__items = list()
		self.__py_node_types_allowed = None
		self.__set_items = self.__set_items_unfiltered
		if not(allowed_py_node_types is None):
			self.__set_filtering_types(allowed_py_node_types)
			self.__set_items = self.__set_items_filtered_by_py_node_type

	def __set_filtering_types(self, types):
		self.__py_node_types_allowed = _err.NotTypeError(types, 'types').raise_if_wrong_arg_for_isinstance()

	def __set_items_unfiltered(self, items=None, selection_if_none=True):
		"""
		Called only if filtering types not provided.
		"""
		items = _def.handle_input(items, selection_if_none)
		if not items:
			self.__items = list()
			return
		self.__items = items

	def __set_items_filtered_by_py_node_type(self, items=None, selection_if_none=True):
		"""
		Called only if filtering types are specified via <allowed_py_node_types> argument.
		"""
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
		self.__set_items(value, False)
