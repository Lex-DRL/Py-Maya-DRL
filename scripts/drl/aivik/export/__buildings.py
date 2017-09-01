__author__ = 'DRL'

import re

from drl.for_maya.ls import pymel as ls

from .__base_class import BaseExport



class Buildings(BaseExport):
	_kept_colors_name_starts = (
		"ground",
		"hill",
		"island",
		"vane",
		"steam"
	)
	_kept_colors_name_starts_f = tuple(
		re.compile(
			r'^{0}[\d_A-Za-z]*$'.format(x.lower())
		)
		for x in _kept_colors_name_starts
	)

	@staticmethod
	def do_keep_color(obj):
		"""
		Checks given object name and tells if the object
		should keep it's vertex-color during cleanup.

		:param obj: <str / PyNode>
		:return: <bool>
		"""
		nm_lower = ls.short_item_name(obj).lower()
		nm_lower = nm_lower.split('.')[0]  # remove component to get a shape name
		return any(
			f.match(nm_lower) for f in Buildings._kept_colors_name_starts_f
		)

	def color_sets_cleanup(self):
		"""
		Removes color sets for anything with not matching name.
		Matching names are listed in _kept_colors_name_starts.
		"""
		self._color_sets_cleanup(Buildings.do_keep_color)
		return self