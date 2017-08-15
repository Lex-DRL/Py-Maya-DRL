__author__ = 'DRL'

from functools import partial as _part

import pymel.core as _pm

from drl_common.utils import group_items as _group_items

from drl.for_maya.ls.convert.components import Poly as _PolyConvert

from math import sqrt as __sqrt

_sqrt_2 = __sqrt(2.0)


class UVs(_PolyConvert):

	def sew_extra_seams(self, resolution=1024, pixel_fraction=0.5):
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