__author__ = 'DRL'

import re

from drl.for_maya.ls import pymel as ls

from .__base_class import BaseExport


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


class Buildings(BaseExport):
	def export(self, overwrite=2, map1_res=2048):
		self.un_turtle().del_not_exported().render_layers_cleanup()
		self.un_parent()
		self.uv_sets_cleanup().uvs_sew(map1_res).color_sets_cleanup()
		self.del_history_smart().mat_faces_to_obj()
		self.del_not_exported()  # one more time, if anything is left after un-parenting
		self._del_object_sets()
		self._del_unused_nodes()
		return self.load_preset().export_dialog(overwrite)

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
			f.match(nm_lower) for f in _kept_colors_name_starts_f
		)

	def color_sets_cleanup(self):
		"""
		Removes color sets for anything with not matching name.
		Matching names are listed in _kept_colors_name_starts.
		"""
		self._color_sets_cleanup(Buildings.do_keep_color)
		return self