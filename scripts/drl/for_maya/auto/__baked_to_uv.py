from drl.for_maya.base_class import PolyItemsProcessorBase as __BaseProcessor
from .cleanup import UVSetsRule as _Rule


class BakedToUVs(__BaseProcessor):
	def __init__(
		self, items=None, selection_if_none=True, hierarchy=False, uv_set_rule='LM_color'
	):
		"""
		:param items: Objects/Shapes/Components to process
		:param hierarchy:
			During any PolyConversions, how to convert transforms with children:
				* True - each Transform is converted to the components of the entire hierarchy.
				* False - only the "direct" children's components are in the result.
			It affects only transforms in the items list.
		:type hierarchy: bool
		:param uv_set_rule:
			Specify the rule for target UV-set(s). E.g.:
				(
					'WindUVs',
					('LM_out', 'LM'),
					1,
					0
				)
			It means: select WindUVs, the 1st, the current UV-set and also: (LM_out if exist, otherwise 'LM').
			For simple cases with single-set processing, you can just pass a string/int.
		:type uv_set_rule: _Rule|str|unicode|int|tuple
		"""
		super(BakedToUVs, self).__init__(items, selection_if_none, hierarchy)
		self.__uv_set_rule = _Rule(uv_set_rule)
		self.__uv_set_rule.is_keep = True

	@property
	def uv_set_rule(self):
		return self.__uv_set_rule

	@uv_set_rule.setter
	def uv_set_rule(self, value):
		self.__uv_set_rule = _Rule(value)
		self.__uv_set_rule.is_keep = True
