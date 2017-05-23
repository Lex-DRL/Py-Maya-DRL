__author__ = 'DRL'

import re
from pymel import core as pm

from drl_common import errors as err
from drl.for_maya import geo, scene
from drl.for_maya.ls import pymel as ls
from drl.for_maya.ui import dialogs
from drl.for_maya.plugins import fbx
from drl.for_maya.auto import cleanup as cl

from . import messages as m



class BaseExport(object):
	_maya_default_objects = (
		'persp',
		'top',
		'front',
		'side'
	)

	def __init__(self, objects=None, selection_if_none=True, save_scene_warning=True, **kwargs_exporter):
		super(BaseExport, self).__init__()
		self._objects = list()
		self.__batch_exporter = fbx.BatchExporter(**kwargs_exporter)

		if save_scene_warning:
			self.__save_changed_scene()  # requires ^ __batch_exporter to already be set
		self.__set_objects(objects, selection_if_none)

	def export_as_asset_static(self, overwrite=2):
		self.un_parent()
		return self.load_preset().export_dialog(overwrite)

	def _plugin(self):
		return self.__batch_exporter.get_exporter().id

	def __save_changed_scene(self):
		def _show_warning():
			"""
			Display the "save scene" warning,

			:return: whether the user needs to be asked once again.
			"""
			changed, choice = scene.DefaultSaveChangesDialog(
				m.SAVE_WARNING, m.SAVE_TITLE,
				m.SAVE_DO, m.SAVE_DON_T, m.SAVE_CANCEL,
				icon=dialogs.confirm_icon.WARNING
			).save_if_changed()

			if not changed or choice == 1:
				return False

			if choice == 0:
				confirm = dialogs.confirm(
					m.ESC_TITLE, m.ESC_MESSAGE,
					yes=(m.YES, m.ESC_YES_TIP), no=(m.NO, m.ESC_NO_TIP)
				)
				if confirm:
					raise fbx.errors.ExportAbortedError(self._plugin())
				return True

			if choice == 2:
				confirm = dialogs.confirm(
					m.DON_T_TITLE, m.DON_T_MESSAGE,
					yes=(m.YES, m.DON_T_YES_TIP), no=(m.NO, m.DON_T_NO_TIP),
					icon=dialogs.confirm_icon.QUESTION
				)
				if confirm:
					return False

			return True

		ask = True
		while ask:
			ask = _show_warning()

	def save_changed_scene(self):
		self.__save_changed_scene()
		return self

	def __set_objects(self, objects=None, selection_if_none=True):
		objects = ls.to_objects(objects, selection_if_none, remove_duplicates=True)
		self._objects = objects

	def set_objects(self, objects=None, selection_if_none=True):
		self.__set_objects(objects, selection_if_none)
		return self

	@property
	def objects(self):
		return self._objects

	@objects.setter
	def objects(self, value):
		self.set_objects(value, False)

	@staticmethod
	def children(obj):
		return list(set(
			ls.to_children(
				obj, False,
				from_shape_transforms=True, keep_source_objects=False
			)
		))

	def get_objects_child_transforms(self):
		"""
		List of all the 1st level children of the specified objects.

		:return: <list of PyNodes> child Transforms.
		"""
		res = list()
		extend_f = res.extend
		children_f = BaseExport.children
		map(
			lambda x: extend_f(children_f(x)),
			self._objects
		)
		return res

	def get_all_exported_objects(self, transforms_only=True, keep_order=False):
		"""
		The list of entire hierarchy of exported objects. I.e., specified objects with their children, grand-children etc.

		:param transforms_only: When True, only exported transforms (not their shapes) are returned.
		:param keep_order: Leave it to false if the order doesn't matter. It will work faster.
		:return: <list of PyNodes>
		"""
		objects = self._objects
		kw_args = dict(
			from_shape_transforms=True,
			keep_shapes=not transforms_only
		)
		if keep_order:
			kw_args['remove_duplicates'] = True
			return ls.to_hierarchy(objects, False, **kw_args)
		return list(set(
			ls.to_hierarchy(objects, False, **kw_args)
		))

	def del_not_exported(self):
		"""
		Remove all the extra objects (not included to the export process).
		"""
		exported = self.get_all_exported_objects()
		parents = ls.all_parents(self._objects, False)
		kept = set(exported + parents)
		removed = [
			x for x in ls.all_objects()
			if not (
				(x in kept) or
				ls.short_item_name(x) in BaseExport._maya_default_objects
			)
		]
		if removed:
			pm.delete(removed)
		return self

	def un_parent(self):
		"""
		Re-parent all the marked objects to the world.
		"""
		self._objects = geo.un_parent(self._objects, False)
		return self

	def cleanup_uv_sets(self, kept_sets_rule=None):
		"""
		Cleans up UV-sets on the meshes selected for export.
			* ensures the 1st set is named "map1".
			* Removes all the extra sets, which don't match to the <kept_sets_rule> definition.

		:param kept_sets_rule: e.g.: (1, ('LM_out', 'LM'), 'windUVs')
		"""
		if not kept_sets_rule:
			return self
		exported = self.get_all_exported_objects(False)
		if not exported:
			return self
		cleaner = cl.uv_sets.UVSets(exported, kept_sets_rule, False)
		cleaner.rename_first_set()
		cleaner.remove_extra_sets()
		return self

	def _cleanup_color_sets(self, match_kept_colors_f=None):
		"""
		Removes color sets for any object that don't match to the rule described by <match_kept_colors_f>.

		:param match_kept_colors_f:
			<function with 1 argument> the rule, returning True if the object needs it's color set to be kept.
				* the checked object (PyNode, Transform) is passed as the argument.
		"""
		from drl.for_maya.geo.components import color_sets as cs
		if match_kept_colors_f is None:
			return self
		if not callable(match_kept_colors_f):
			raise err.WrongTypeError(
				match_kept_colors_f, var_name='match_kept_colors_f', types_name='callable'
			)

		exported = [
			x for x in self.get_all_exported_objects()
			if ls.to_shapes(x, False, exact_type=pm.nt.Mesh)
		]
		removed_for = [x for x in exported if not match_kept_colors_f(x)]
		cs.delete_all_sets(removed_for, False)
		return self

	def del_object_sets(self):
		cl.del_all_object_sets()
		return self

	def del_unused_nodes(self):
		cl.del_unused_nodes()
		return self

	def combine_child_groups(self, ends_with='_islanddn', matching_f=None):
		"""
		Under each marked object, find child groups matching the condition
		and merge each of them to a single object, with transforms matching to the parent.

		Optional arguments define the rule selecting main-object's children to be combined.

		:param ends_with: <str> the name of child (under the marked object) converted to lowercase has to end with this substring.
		:param matching_f: <function with 1 input argument>
		* When custom function passed, it's the check itself, returning True/False. True = combine this object's children.
		* When None, the default match function is used, which simply compares the name of the object to <ends_with>.
		"""
		ends_with = err.NotStringError(ends_with, 'ends_with').raise_if_needed_or_empty().lower()
		if matching_f is None:
			matching_f = lambda x: ls.short_item_name(x).lower().endswith(ends_with)
		if not callable(matching_f):
			raise err.WrongTypeError(matching_f, var_name='matching_f', types_name='callable')

		def _combine_single_child_group(combined_group, parent):
			"""
			If the given group  doesn't have shape, but has children:

			* merge them
			* re-parent back to where it was
			* rename with the same name that group had
			* freeze transform
			* reset pivot
			:param combined_group: <pm.nt.Transform> the group which children will be combined to replace it.
			:param parent: the parent group of this one (Island-group relatively to _IslandDn).
			:return: <list> containing either 0 or 1 object: the combined one.
			"""
			combined_group = err.WrongTypeError(combined_group, pm.nt.Transform, 'child_group').raise_if_needed()
			res = list()
			if pm.listRelatives(combined_group, shapes=1):
				return res
			children = BaseExport.children(combined_group)
			if not children:
				return res
			name = ls.short_item_name(combined_group)

			if len(children) < 2:
				combined = pm.parent(children[0], parent, absolute=1)[0]
				pm.delete(combined_group)
			else:
				combined = pm.polyUnite(children, ch=0, mergeUVSets=1)[0]
				combined = pm.parent(combined, parent, absolute=1)[0]

			combined = pm.rename(combined, name)
			geo.freeze_transform(combined, False)
			pm.delete(combined, ch=1)
			return geo.reset_pivot(combined, False)


		def _process_single_group(group):
			"""
			Combine all the matching child groups (IslandDn) for the given parent group (Island itself).
			:param group: parent transform (Island group)
			:return: list of combined objects
			"""
			group = err.WrongTypeError(group, pm.nt.Transform, 'group').raise_if_needed()
			children = BaseExport.children(group)
			to_combine = [c for c in children if matching_f(c)]
			res = list()
			for combined in to_combine:
				res.extend(_combine_single_child_group(combined, group))
			return res

		objects = self._objects
		for o in objects:
			_process_single_group(o)
		return self

	def load_preset(self, preset='AIVIK-Geo'):
		self.__batch_exporter.load_preset(preset)
		return self

	def export_to(self, folder, overwrite=2):
		"""
		Performs export of each parent object to it's own FBX file in the given folder.

		:param folder: <str> path to the folder
		:param overwrite: <int>, whether existing file is overwritten:

			* 0 - don't overwrite (an error is thrown if file already exist)
			* 1 - overwrite
			* 2 - confirmation dialog will pop up if file already exist
		:return: <list of strings> paths of exported FBX files.
		"""
		exp = self.__batch_exporter
		objects = self._objects
		return exp.set_folder(folder).set_groups(objects).export_all_groups(overwrite)

	def export_dialog(self, overwrite=2):
		"""
		Performs export of each parent object to it's own FBX file.
		The folder for export is selected interactively by a user.

		:param overwrite: <int>, whether existing file is overwritten:

			* 0 - don't overwrite (an error is thrown if file already exist)
			* 1 - overwrite
			* 2 - confirmation dialog will pop up if file already exist
		:return: <list of strings> paths of exported FBX files.
		"""
		exp = self.__batch_exporter
		objects = self._objects
		return exp.set_groups(objects).export_all_groups_dialog(overwrite)

	def del_history_smart(self, before_deformers_only=False):
		"""
		Delete history on all the exported objects, the smart way.

		I.e., for deformed models, <Delete Non-Deformer History> is used.

		:param before_deformers_only:
			<bool>, affects deformed objects only.

			Remove only the part of history that occur before the deformers.
				* When **False** (default), all the non-deformer modeling history is removed.
		"""
		objects = self.get_all_exported_objects()
		cl.history.delete_smart(objects, False, before_deformers_only)
		return self



class IslandsPVE(BaseExport):
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
	_re_kept_colors_tuple_exact_case = tuple(map(
		lambda x: re.compile(
			r'^.*_{0}[\dA-Za-z]*$'.format(x)
		),
		_kept_colors_name_parts
	))
	# (lowercase-comparison match, expected name) functions:
	_re_kept_colors_tuple_ignore_case = tuple(map(
		lambda x: (re.compile(
			r'^.*_{0}[\dA-Za-z]*$'.format(x.lower())
		), x),
		_kept_colors_name_parts
	))

	def export_as_pve_islands(self, overwrite=2):
		exp = self.un_parent().del_trees_mesh().combine_islands_dn().combine_waterfalls()
		return exp.load_preset().export_dialog(overwrite)

	@staticmethod
	def match_as_trees_group(parent_name, child):
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
		child = err.WrongTypeError(child, pm.nt.Transform, 'child').raise_if_needed()
		child_nm = ls.short_item_name(child)
		match = IslandsPVE._match_trees.match(child_nm)
		if match is None:
			return 0
		# we've got match now
		if not parent_name.endswith(match.group(1)):
			return 2
		return 1

	@staticmethod
	def match_as_enemy_base(island_child):
		island_child = err.WrongTypeError(island_child, pm.nt.Transform, 'island_child').raise_if_needed()
		child_nm = ls.short_item_name(island_child).lower()
		return bool(
			IslandsPVE._match_enemy_base.match(child_nm)
		)

	def get_enemy_base_transforms(self):
		"""
		All the EnemyBase root transform. It's either an EnemyBase object itself, or it's group.

		:return: <list of PyNodes> Transforms.
		"""
		children = self.get_objects_child_transforms()
		return [x for x in children if IslandsPVE.match_as_enemy_base(x)]

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
				match = IslandsPVE.match_as_trees_group(parent_name, child)
				if match in (0, 1):
					return bool(match), ignore_warning

				# match == 2:
				if ignore_warning:
					return True, ignore_warning

				msg = m.TREES_MESSAGE.format(ls.short_item_name(child), parent_name)
				choice = dialogs.confirm(
					title=m.TREES_TITLE, message=msg,
					icon=dialogs.confirm_icon.QUESTION,
					yes=(m.YES, m.TREES_YES_TIP),
					no=(m.NO, m.TREES_NO_TIP),
					extra_buttons=((m.YES_ALL, m.TREES_YES_ALL_TIP),),
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

	def cleanup_color_sets(self):
		"""
		Removes color sets for anything with not matching name.
		Matching names are listed in _kept_colors_name_parts.

		If some object has the matching name, but in the wrong case ('lower' or 'UPPER'),
		the warning is shown asking if you want to keep it's colors, cleanup (as ll other meshes) or abort export entirely.
		"""
		def _is_color_kept(node):
			nm = ls.short_item_name(node)
			is_exact_match = any([
				x.match(nm) for x in IslandsPVE._re_kept_colors_tuple_exact_case
			])
			if is_exact_match:
				return True
			# exact match not found, trying a case-insensitive match:
			nm_lower = nm.lower()
			for m_f, m_nm in IslandsPVE._re_kept_colors_tuple_ignore_case:
				if m_f.match(nm_lower):
					msg = m.COLOR_SETS_MESSAGE.format(nm, m_nm)
					choice = dialogs.confirm(
						title=m.COLOR_SETS_TITLE, message=msg,
						icon=dialogs.confirm_icon.QUESTION,
						yes=(m.YES, m.COLOR_SETS_YES_TIP),
						no=(m.COLOR_SETS_CANCEL, m.COLOR_SETS_CANCEL_TIP),
						extra_buttons=((m.NO, m.COLOR_SETS_NO_TIP),),
						default_if_not_maya=1
					)
					if not choice:
						raise fbx.errors.ExportAbortedError(self._plugin())
					if choice == 1:
						return True
			return False

		self._cleanup_color_sets(_is_color_kept)
		return self

	def combine_islands_dn(self):
		return self.combine_child_groups()

	def combine_waterfalls(self):
		return self.combine_child_groups(
			matching_f=lambda x: ls.short_item_name(x).lower().rstrip('1234567890s').endswith('_waterfall')
		)
