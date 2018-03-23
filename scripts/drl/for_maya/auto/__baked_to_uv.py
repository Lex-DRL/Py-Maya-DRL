from pymel.core.datatypes import Vector, Matrix
from .cleanup import UVSetsRule as Rule
from drl.for_maya.base_class import PolyItemsProcessorBase as __BaseProcessor
from drl_common.srgb import linear_to_srgb


class BakedToUVs(__BaseProcessor):
	"""
	Convert LightMap from vertex colors to UVs.
	"""
	_def_bright = Vector(1, 1, 1)
	_def_color = Vector(0, 0.132934, 0.4)

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
		:type uv_set_rule: str|unicode|int|tuple|Rule
		"""
		super(BakedToUVs, self).__init__(items, selection_if_none, hierarchy)
		self.__uv_set_rule = Rule(uv_set_rule)
		self.__uv_set_rule.is_keep = True

	@property
	def uv_set_rule(self):
		"""
		Rule to detect target UV-set.
		"""
		return self.__uv_set_rule  # type: _Rule

	@uv_set_rule.setter
	def uv_set_rule(self, value):
		"""
		Rule to detect target UV-set.
		"""
		self.__uv_set_rule = Rule(value)
		self.__uv_set_rule.is_keep = True

	@staticmethod
	def uv_to_rgb_mtx(color=None, bright=None):
		"""
		Restore LM color from UV space, where:
			* x (U) axis represents `0 to LM tint color` (to blue)
			* y (V) axis represents `0 to bright` (to pure white)
		``rgb = uv_vector * uv_to_rgb_mtx()``

		:param color:
			U axis (in RGB space).
			Default: (0, 0.132934, 0.4) - used if `None` provided.
		:type color: None|list[int|float]|tuple[int|float]|Vector
		:param bright:
			V axis (in RGB space).
			Default: (1, 1, 1) - used if `None` provided.
		:type bright: None|list[int|float]|tuple[int|float]|Vector
		:return: matrix
		"""
		v_clr = Vector(color) if color else BakedToUVs._def_color  # type: Vector
		v_wht = Vector(bright) if bright else BakedToUVs._def_bright  # type: Vector
		v_cross = v_clr.cross(v_wht)  # type: Vector
		uv_to_rgb = Matrix(v_clr, v_wht, v_cross).transpose()  # type: Matrix
		return uv_to_rgb

	@staticmethod
	def rgb_to_uv_mtx(color=None, bright=None):
		"""
		Generates the matrix projecting the baked LM color to UV space, where:
			* x (U) axis represents `0 to LM tint color` (to blue)
			* y (V) axis represents `0 to bright` (to pure white)
		``uv_vector = rgb * rgb_to_uv_mtx()``

		The 3rd (z) component of UV vector can be discarded to `VectorN`:
			``uv_vector[:-1]``

		:param color:
			U axis (in RGB space).
			Default: (0, 0.132934, 0.4) - used if `None` provided.
		:type color: None|list[int|float]|tuple[int|float]|Vector
		:param bright:
			V axis (in RGB space).
			Default: (1, 1, 1) - used if `None` provided.
		:type bright: None|list[int|float]|tuple[int|float]|Vector
		:return: matrix
		"""
		uv_to_rgb = BakedToUVs.uv_to_rgb_mtx(color, bright)
		rgb_to_uv = uv_to_rgb.inverse()  # type: Matrix
		return rgb_to_uv
