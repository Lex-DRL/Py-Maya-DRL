from pymel import core as pm
from pymel.core.datatypes import Vector, Matrix
from .cleanup import UVSetsRule as Rule
from drl.for_maya.ls import pymel as ls
from drl.for_maya.base_class import PolyObjectsProcessorBase
from drl_common import errors as err
from drl_common.srgb import linear_to_srgb as to_srgb


class BakedToUVs(PolyObjectsProcessorBase):
	"""
	Convert LightMap from vertex colors to UVs.
	"""
	_def_bright = Vector(1, 1, 1)
	_def_color = Vector(0, 0.132934, 0.4)
	_def_color_srgb = Vector(0, 0.171825, 0.4)

	def __init__(
		self, items=None, selection_if_none=True, hierarchy=False,
		srgb=True, bright=None, color=None,
		color_set='baked_tpIllumination', uv_set_rule='LM_color'
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
		:param srgb:
			Given objects' colors will be processed and stored to UVs in sRGB color space.
		:type srgb: bool
		:param bright:
			The color axis pointing to the brightest pixel. It will be the resulting **V**.
			By default, it's (1, 1, 1).
		:type bright: Vector
		:param color:
			The color axis pointing to the direction of the most saturated basic color.
			It will be the resulting **U**.
			By default:
				* (0, 0.171825, 0.4) is used in srgb mode
				* (0, 0.132934, 0.4) otherwise.
		:type color: Vector
		"""
		super(BakedToUVs, self).__init__(items, selection_if_none, hierarchy)
		self.__uv_set_rule = Rule(uv_set_rule)
		self.__uv_set_rule.is_keep = True
		self.__color_set = err.NotStringError(
			color_set, 'color_set'
		).raise_if_needed_or_empty()
		self.__srgb = bool(srgb)
		self.__bright = BakedToUVs.__prepare_bright_value(bright)
		self.__color = self.__prepare_color_value(color)

	@staticmethod
	def __prepare_bright_value(bright):
		return (
			Vector(bright) if bright
			else BakedToUVs._def_bright
		)

	def __prepare_color_value(self, color):
		if color:
			return Vector(color)
		return (
			BakedToUVs._def_color_srgb if self.__srgb
			else BakedToUVs._def_color
		)

	# region Properties

	@property
	def color_set(self):
		return self.__color_set

	@color_set.setter
	def color_set(self, value):
		self.__color_set = err.NotStringError(
			value, 'color_set property'
		).raise_if_needed_or_empty()

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

	@property
	def srgb(self):
		return self.__srgb

	@srgb.setter
	def srgb(self, value):
		self.__srgb = bool(value)

	@property
	def bright(self):
		return self.__bright

	@bright.setter
	def bright(self, value):
		self.__bright = BakedToUVs.__prepare_bright_value(value)

	@property
	def color(self):
		return self.__color

	@color.setter
	def color(self, value):
		self.__color = self.__prepare_color_value(value)

	# endregion

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
		:rtype: Matrix
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
		:rtype: Matrix
		"""
		uv_to_rgb = BakedToUVs.uv_to_rgb_mtx(color, bright)
		rgb_to_uv = uv_to_rgb.inverse()  # type: Matrix
		return rgb_to_uv

	@staticmethod
	def _prepare_uv_set(obj, rule):
		"""
		Prepare a target UV-set for the given single object.
		I.e.:
			* ensure it exists (based on the provided rule)
			* switch to this set
			* create default UVs (by planar projection)
			* cut them at hard edges

		:type rule: UVSetsRule
		:return: shape and the name of target set
		"""
		err.WrongTypeError(obj, pm.PyNode, 'obj').raise_if_needed()
		err.WrongTypeError(rule, Rule, 'rule').raise_if_needed()
		pre_sel = pm.ls(sl=1)
		pm.delete(obj, ch=1)

		shape_t = pm.nt.Mesh
		shape = (
			obj if isinstance(obj, shape_t)
			else ls.to_shapes(obj, False, exact_type=shape_t, remove_duplicates=True)[0]
		)  # type: shape_t
		target_set = rule.kept_sets_for_object(obj, False)
		if not target_set:
			target_set = rule.rule[0][0]  # type: str
			err.NotStringError(target_set, 'target_set').raise_if_needed_or_empty()
			target_set = shape.createUVSet(target_set)  # type: str
		else:
			target_set = target_set[0]  # type: str
			shape.clearUVs(target_set)
		shape.setCurrentUVSetName(target_set)
		pm.delete(shape, ch=1)
		pm.polyProjection(
			shape, ch=0, insertBeforeDeformers=1, keepImageRatio=1,
			mapDirection='y', type='planar', uvSetName=target_set
		)

		pm.select(shape.e, r=1)  # select all shape edges
		pm.polySelectConstraint(m=2, t=0x8000, w=2, sm=1)  # keep only hard edges
		pm.polySelectConstraint(disable=1, m=0)
		hard_edges = pm.ls(sl=1)
		pm.polyMapCut(hard_edges, ch=0)

		pm.select(pre_sel, r=1)
		return shape, target_set

	@staticmethod
	def __transfer_to_uv(shape, color_set, uv_set, mtx, get_color_f):
		"""
		For each UV in given UV-set of the shape:
			*
				read all the color from vertex-faces with get_color_f(vf) -
				UVs are already have to be cut according to hard edges.
			* calc average vertexFace-colors of each UV
			* re-set vertexFace-colors with average value
			* transform color to 2D-space with the given matrix
			* pass resulting XY coordinates as UVs
		This function is generic for color-transform either in linear or sRGB space.
		"""
		shape.setCurrentColorSetName(color_set)
		shape.setCurrentUVSetName(uv_set)
		uvs = shape.map
		for uv in uvs:
			vfs = pm.polyListComponentConversion(uv, toVertexFace=True)
			if not vfs:
				continue
			vfs = pm.ls(vfs, fl=1)  # flatten
			avg_clr = sum(
				Vector(get_color_f(vf))
				for vf in vfs
			) / len(vfs)  # type: Vector
			pm.polyColorPerVertex(vfs, rgb=avg_clr, notUndoable=1)
			# transform to UV space:
			avg_clr = mtx * avg_clr  # type: Vector
			u, v = avg_clr[:2]
			pm.polyEditUV(uv, relative=False, uValue=u, vValue=v, uvSetName=uv_set)

	@staticmethod
	def _transfer_to_uv_linear(shape, color_set, uv_set, mtx):
		"""
		Transform linear vertex colors to UVs.

		:type shape: pm.nt.Mesh
		:type color_set: str
		:type uv_set: str
		:param mtx: RGB-to-UV transformation matrix.
		:type mtx: Matrix
		"""
		BakedToUVs.__transfer_to_uv(
			shape, color_set, uv_set, mtx,
			lambda vf: pm.polyColorPerVertex(vf, q=1, rgb=1, notUndoable=1)
		)

	@staticmethod
	def _transfer_to_uv_srgb(shape, color_set, uv_set, mtx):
		"""
		Transform linear vertex colors to sRGB and then to UVs.

		:type shape: pm.nt.Mesh
		:type color_set: str
		:type uv_set: str
		:param mtx: RGB-to-UV transformation matrix.
		:type mtx: Matrix
		"""
		BakedToUVs.__transfer_to_uv(
			shape, color_set, uv_set, mtx,
			lambda vf: to_srgb(pm.polyColorPerVertex(vf, q=1, rgb=1, notUndoable=1))
		)

	def transfer(self):
		"""
		Process all the provided objects,
		transferring vertex-color to the given UV-set.

		:return:
			list of pairs:
				* processed shape
				* it's UV-set
		:rtype: list[tuple[pm.PyNode,str]]
		"""
		objects = self.items
		transfer = (
			self._transfer_to_uv_srgb if self.srgb
			else self._transfer_to_uv_linear
		)
		matrix = self.rgb_to_uv_mtx(self.color, self.bright)
		res = list()
		res_append = res.append
		for obj in objects:
			shape, uv_set = self._prepare_uv_set(obj, self.uv_set_rule)
			transfer(shape, self.color_set, uv_set, matrix)
			res_append((shape, uv_set))
		return res
