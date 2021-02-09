__author__ = 'Lex Darlog (DRL)'

from functools import partial as _part

import pymel.core as _pm

from drl_common.utils import group_items as _group_items

from drl.for_maya.geo.components import uv_sets as _sets
from drl.for_maya.ls.convert.components import Poly as _PolyConvert

from math import sqrt as __sqrt

_sqrt_2 = __sqrt(2.0)


class UVs(_PolyConvert):
	def __init__(self, items=None, selection_if_none=True, hierarchy=False, uv_set=None):
		super(UVs, self).__init__(
			items=items, selection_if_none=selection_if_none,
			hierarchy=hierarchy
		)
		self.uv_set = uv_set

	def switch_uv_set(self, uv_set=None):
		"""
		Sets the currently active UV set for the specified items.

		:param uv_set:
			<int / string>

			The number or the name for the set:
				* None/0 - current (don't change)
				* <str> - name
				* <int> - 1-based UV-set number
		:return: list of <Mesh> shapes for which UV-set has been changed.
		"""
		return _sets.set_current(self.get_geo_items(), uv_set, selection_if_none=False)

	def sew_extra_seams(self, resolution=1024, pixel_fraction=0.5):
		self.switch_uv_set(self.uv_set)

		uvs = self.to_uvs(flatten=False)
		if not uvs:
			return self

		prev_sl = _pm.ls(sl=1)
		prev_hl = _pm.ls(hl=1)

		uvs_per_shape = _group_items(uvs, key_f=lambda x: x.node().name())  # list of tuples

		allowed_delta = float(pixel_fraction) * _sqrt_2 * 1.001 / resolution
		process_single_shape_uvs = _part(
			_pm.polyMergeUV,
			ch=False, worldSpace=False, distance=allowed_delta
		)
		map(process_single_shape_uvs, uvs_per_shape)

		try:
			_pm.select(prev_sl, r=1)
		except:
			pass

		try:
			_pm.hilite(prev_hl, r=1)
		except:
			pass

		return self