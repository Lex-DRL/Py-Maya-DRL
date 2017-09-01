__author__ = 'DRL'

import re
from pymel import core as pm

from drl_common import errors as err
from drl.for_maya import geo
from drl.for_maya.ls import pymel as ls
from drl.for_maya.ui import dialogs
from drl.for_maya.plugins import fbx

from .messages import island as m, common as m_c

from drl.for_maya.py_node_types import transform as _t_transform

from .__base_class import BaseExport


_match_trees = re.compile(r'^([\d_A-Za-z]+)_Trees\d*$')
_match_enemy_base = re.compile(r'.*enemy[\dA-Za-z]*base.*')
_kept_colors_name_parts = (
	'IslandUp',
	'GroundPatch',
	'Rock',
	'Flag',
	'IslandDn'
)
# exact-match functions for "keep colors" check:
_re_kept_colors_tuple_exact_case = tuple(
	re.compile(
		r'^.*_{0}[\dA-Za-z]*$'.format(x)
	)
	for x in _kept_colors_name_parts
)
# (lowercase-comparison match, expected name) functions:
_re_kept_colors_tuple_ignore_case = tuple(
	(
		re.compile(
			r'^.*_{0}[\dA-Za-z]*$'.format(x.lower())
		),
		x
	)
	for x in _kept_colors_name_parts
)


def _match_as_trees_group(parent_name, child):
	"""
	Check if the given child object seems to be a <Trees> group under <Island> group.

	:param parent_name: <str> the name of the parent (Island group).
	:param child: <PyNode:Transform> Object located right under island group in hierarchy.
	:return: <int>:
	* 0 - it's just an abitrary island objec | another group (i.e., Roads)
	* 1 - Match, it's a Trees group
	* 2 - Partial match: Child's name is '*_Trees', but beginning doesn't match the island-group's name.
	"""
	parent_name = err.NotStringError(parent_name, 'parent_name').raise_if_needed_or_empty()
	child = err.WrongTypeError(child, _t_transform, 'child').raise_if_needed()
	child_nm = ls.short_item_name(child)
	match = _match_trees.match(child_nm)
	if match is None:
		return 0
	# we've got match now
	if not parent_name.endswith(match.group(1)):
		return 2
	return 1


def _match_as_enemy_base(island_child):
	island_child = err.WrongTypeError(island_child, _t_transform, 'island_child').raise_if_needed()
	child_nm = ls.short_item_name(island_child).lower()
	return bool(
		_match_enemy_base.match(child_nm)
	)


class IslandsPVE(BaseExport):
	def export(self, overwrite=2, map1_res=2048):
		self.un_turtle().del_not_exported().render_layers_cleanup()
		self.del_trees_mesh().del_enemy_base_mesh()
		self.combine_islands_dn().combine_waterfalls()
		self.un_parent()
		self.uv_sets_cleanup().uvs_sew(map1_res).color_sets_cleanup()
		self.del_history_smart().mat_faces_to_obj()
		self.del_not_exported()  # one more time, if anything is left after un-parenting
		self._del_object_sets()
		self._del_unused_nodes()
		return self.load_preset().export_dialog(overwrite)

	def get_enemy_base_transforms(self):
		"""
		All the EnemyBase root transform. It's either an EnemyBase object itself, or it's group.

		:return: <list of PyNodes> Transforms.
		"""
		children = self.get_objects_child_transforms()
		return [x for x in children if _match_as_enemy_base(x)]

	def get_trees(self):
		"""
		Get list of child objects that seem to bee trees. I.e. they're under sub-group, which:

		* Is called "*_Trees"
		* Is just a group, not a mesh (has no shapes right under it, only children).
		* It has child transforms
		"""
		def _find_trees_groups(parent_name, island_children):
			"""
			Filter given objects, leaving only those that seem to be <Trees> groups.
			Normally, it should return only 1 object.

			:return: list of elements from <island_children> that seem to be Tress groups.
			"""
			partial_match_ok = False
			res = list()

			def _bool_match(child, ignore_warning):
				"""
				check if a given object in <Island> group seems to be Trees group

				:param child: the object checked.
				:param ignore_warning: partial_match_ok, silence the following warnings
				:return: <bool> is it a trees group, <bool> partial_match_ok
				"""
				match = _match_as_trees_group(parent_name, child)
				if match in (0, 1):
					return bool(match), ignore_warning

				# match == 2:
				if ignore_warning:
					return True, ignore_warning

				msg = m.TREES_MESSAGE.format(ls.short_item_name(child), parent_name)
				choice = dialogs.confirm(
					title=m.TREES_TITLE, message=msg,
					icon=dialogs.confirm_icon.QUESTION,
					yes=(m_c.YES, m.TREES_YES_TIP),
					no=(m_c.NO, m.TREES_NO_TIP),
					extra_buttons=((m_c.YES_ALL, m.TREES_YES_ALL_TIP),),
					default_if_not_maya=1
				)
				if choice == 2:
					ignore_warning = True
				return bool(choice), ignore_warning

			for c in island_children:
				is_tree_gr, partial_match_ok = _bool_match(c, partial_match_ok)
				if is_tree_gr:
					res.append(c)
			return res

		def _get_single_island_trees(obj):
			children = BaseExport.children(obj)
			nm = ls.short_item_name(obj)
			tree_groups = _find_trees_groups(nm, children)
			island_trees = list()
			for tree_gr in tree_groups:
				island_trees.extend(BaseExport.children(tree_gr))
			return island_trees

		trees = list()
		objects = self._objects
		for o in objects:
			trees.extend(_get_single_island_trees(o))
		return trees

	def del_trees_mesh(self):
		"""
		Keep only transforms for trees found under given Island groups.

		Yes, given objects are expected to be Island groups.
		"""
		trees = self.get_trees()
		if not trees:
			return self

		trees = geo.instance_to_object(trees, False)
		for t in trees:
			pm.delete(pm.listRelatives(t, children=1))
		return self

	def del_enemy_base_mesh(self):
		"""
		Keep only transforms for EnemyBases found under given Island groups.

		Yes, given objects are expected to be Island groups.
		"""
		bases = self.get_enemy_base_transforms()
		if not bases:
			return self

		bases = geo.instance_to_object(bases, False)
		for t in bases:
			pm.delete(pm.listRelatives(t, children=1))
		return self

	def color_sets_cleanup(self):
		"""
		Removes color sets for anything with not matching name.
		Matching names are listed in _kept_colors_name_parts.

		If some object has the matching name, but in the wrong case ('lower' or 'UPPER'),
		the warning is shown asking if you want to keep it's colors, cleanup (as ll other meshes) or abort export entirely.
		"""
		def _is_color_kept(node):
			nm = ls.short_item_name(node)
			is_exact_match = any([
				x.match(nm) for x in _re_kept_colors_tuple_exact_case
			])
			if is_exact_match:
				return True
			# exact match not found, trying a case-insensitive match:
			nm_lower = nm.lower()
			for m_f, m_nm in _re_kept_colors_tuple_ignore_case:
				if m_f.match(nm_lower):
					msg = m.COLOR_SETS_MESSAGE.format(nm, m_nm)
					choice = dialogs.confirm(
						title=m.COLOR_SETS_TITLE, message=msg,
						icon=dialogs.confirm_icon.QUESTION,
						yes=(m_c.YES, m.COLOR_SETS_YES_TIP),
						no=(m.COLOR_SETS_CANCEL, m.COLOR_SETS_CANCEL_TIP),
						extra_buttons=((m_c.NO, m.COLOR_SETS_NO_TIP),),
						default_if_not_maya=1
					)
					if not choice:
						raise fbx.errors.ExportAbortedError(self._plugin())
					if choice == 1:
						return True
			return False

		self._color_sets_cleanup(_is_color_kept)
		return self

	def combine_islands_dn(self):
		return self._combine_child_groups()

	def combine_waterfalls(self):
		return self._combine_child_groups(
			matching_f=lambda x: ls.short_item_name(x).lower().rstrip('1234567890s').endswith('_waterfall')
		)