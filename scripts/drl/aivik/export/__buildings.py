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
		"""
		:param overwrite:
			<int>, whether existing file is overwritten:
				* 0 - don't overwrite (an error is thrown if file already exist)
				* 1 - overwrite
				* 2 - confirmation dialog will pop up if file already exist
		:param map1_res:
			<int>

			Resolution of the texture on main UV-set (map1).
			Used to sew border UVs which are closer then 1px.
		:return: <list of strings> paths of exported FBX files.
		"""
		self.un_turtle().del_not_exported().render_layers_cleanup()
		self.un_parent()
		self.uv_sets_cleanup().uvs_sew(map1_res).color_sets_cleanup()
		self.del_history_smart()
		# TODO: replace with forcefully-set initial mat:
		# self.mat_faces_to_obj()  # takes too long to execute.
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