__author__ = 'DRL'

from pymel import core as pm
from pymel.core.datatypes import Vector, Point
from drl.for_maya.base_class import PolyObjectsProcessorBase


class ExplodeParts(PolyObjectsProcessorBase):
	"""
	Offset multiple objects radially, each in the direction of it's own bbox center.
	"""
	__default_distance = 1.0

	def __init__(
		self, items=None, selection_if_none=True, hierarchy=False,
		distance=0
	):
		"""
		Offset multiple objects radially, each in the direction of it's own bbox center.

		:param distance:
			* if None or false, try to automatically detect the distance:
				*
					First, all the selected objects are checked for how far away
					their center is form their local zero (parent/world).
					The maximum is chosen.
				* If the found maximum is still zero, use the default distance (1.0)
			* If any meaningful distance is given, use it.
		:type distance: int|float|None
		"""
		super(ExplodeParts, self).__init__(items, selection_if_none, hierarchy)
		self.distance = distance

	@staticmethod
	def __local_center(obj):
		"""
		Position of the bbox center relative to the parent (to world 0 if no parent).
		"""
		res = obj.getBoundingBox(invisible=False, space='object').center()  # type: Point
		return Vector(res)

	def detect_distance(self):
		"""
		Returns
			* distance argument if it's non-zero.
			* Otherwise - detect the longest distance to the center of items.
			* If even it is zero - return the default (1.0).
		"""
		dist = self.distance
		if dist is not None and dist > 0:
			return float(dist)
		# we're in auto mode, let's try to actually detect the best distance:
		dist = max(
			(self.__local_center(x).length() for x in self.items)
		)  # type: float
		return dist if dist > 0 else self.__default_distance

	@staticmethod
	def __offset_single_obj(obj, distance):
		v = ExplodeParts.__local_center(obj)
		l = v.length()
		if l > 0:
			v = (v / l) * distance  # type: Vector
		else:
			v = Vector(1, 0, 0) * distance  # type: Vector
		t_attr = obj.t  # type: pm.Attribute
		prev = t_attr.get()  # type: Vector
		t_attr.set(prev + v)
		return v

	def offset(self):
		"""
		Offset each object in the direction of it's bbox center.
		If bbox center is in zero, direction is (1, 0, 0) in local space.
		"""
		distance = self.detect_distance()
		return [
			self.__offset_single_obj(o, distance) for o in self.items
		]
