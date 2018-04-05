__author__ = 'DRL'

from pymel.core import PyNode

import re

from drl.for_maya.ls import pymel as ls
from drl_common import errors as err

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
	def export(
		self, overwrite=2, map1_res=2048,
		kept_colors_regexps=None, kept_colors_lowercase=True
	):
		"""
		:param overwrite:
			whether existing file is overwritten:
				* 0 - don't overwrite (an error is thrown if file already exist)
				* 1 - overwrite
				* 2 - confirmation dialog will pop up if file already exist
		:type overwrite: int
		:param map1_res:
			Resolution of the texture on main UV-set (map1).
			Used to sew border UVs which are closer then 1px.
		:type map1_res: int
		:param kept_colors_regexps:
			If specified, this regexp(s) define the rule which object's colors are kept.
			Otherwise, the default rule is used, keeping colors only for those objects
			which usually require them.
		:type kept_colors_regexps: None|str|unicode|tuple[str|unicode]
		:param kept_colors_lowercase:
			If `True`, the name of the object is matched to regexp in lowercase.
			(regex string should be in lowercase, too)
		:return: paths of exported FBX files.
		:rtype: list[str|unicode]
		"""
		self.un_turtle().del_not_exported().render_layers_cleanup()
		self.un_parent()
		self.uv_sets_cleanup().uvs_sew(map1_res)
		self.color_sets_cleanup(kept_colors_regexps, kept_colors_lowercase)
		self.del_history_smart()
		# TODO: replace with forcefully-set initial mat:
		# self.mat_faces_to_obj()  # takes too long to execute.
		self.del_not_exported()  # one more time, if anything is left after un-parenting
		self._del_object_sets()
		self._del_unused_nodes()
		return self.load_preset().export_dialog(overwrite)

	def color_sets_cleanup(self, kept_regexps=None, lowercase=True):
		"""
		Removes color sets for anything with not matching name.

		:param kept_regexps:
			If specified, this regexp(s) define the rule which object's colors are kept.
			Otherwise, the default rule is used, keeping colors only for those objects
			which usually require them.
		:type kept_regexps: None|str|unicode|tuple[str|unicode]
		:param lowercase:
			If `True`, the name of the object is matched to regexp in lowercase.
			(regex string should be in lowercase, too)
		"""
		def get_re_fs(regexps):
			"""
			Generate a tuple of compiled regexp objects from
			the provided regexp(s) arg.
			"""
			if regexps is None or not regexps:
				return _kept_colors_name_starts_f

			re_type = type(re.compile('qqq'))
			if isinstance(regexps, (str, unicode, re_type)):
				regexps = (regexps,)

			def _process_single(regex):
				if isinstance(regex, re_type):
					return regex
				regex = err.NotStringError(regex).raise_if_needed_or_empty()
				# if ignore_case:  # should be already lowercase in regex itself
				# 	regex = regex.lower()
				return re.compile(regex)

			return tuple(_process_single(r) for r in regexps)

		kept_fs = get_re_fs(kept_regexps)
		get_obj_name = (  # function converting PyNode to name
			lambda x: ls.short_item_name(x).lower()
			if lowercase
			else ls.short_item_name
		)

		def does_name_match(obj):
			"""
			Checks given object name and tells if the object
			should keep it's vertex-color during cleanup.

			:type obj: str|unicode|PyNode
			:rtype: bool
			"""
			nm_lower = get_obj_name(obj)
			nm_lower = nm_lower.split('.')[0]  # remove component to get a shape name
			return any(
				f.match(nm_lower) for f in kept_fs
			)

		match_all = re.compile('.*')
		name_check_f = (
			lambda x: True
			if any(fm == match_all for fm in kept_fs)
			else does_name_match
		)

		self._color_sets_cleanup(name_check_f)
		return self
