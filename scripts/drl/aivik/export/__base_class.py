__author__ = 'DRL'

from pymel import core as pm

from drl_common import errors as err
from drl.for_maya import geo, scene
from drl.for_maya.ls import pymel as ls
from drl.for_maya.ui import dialogs
from drl.for_maya.plugins import fbx
from drl.for_maya.auto import cleanup as cl

from .messages import common as m

from drl.for_maya.py_node_types import transform as _t_transform


_maya_default_objects = (
	'persp',
	'top',
	'front',
	'side'
)


# TODO:
# * move UV-shells to range (both LM and map1)
# * replace mat_faces_to_obj() with forcefully-setting initial mat
# * unlocking normals / sewing them if they're about the same
# * merging vertices (for normal-reversed polygons acting as two sides)
# * (maybe) auto-detect texture resolution for map1 sewing
# * remove shadow-caster objects
class BaseExport(object):
	def __init__(
		self, objects=None, selection_if_none=True, save_scene_warning=True,
		**kwargs_exporter
	):
		super(BaseExport, self).__init__()
		self._objects = list()
		self.__batch_exporter = fbx.BatchExporter(**kwargs_exporter)

		if save_scene_warning:
			self.__save_changed_scene()  # requires ^ __batch_exporter to already be set
		self.__set_objects(objects, selection_if_none)

	@property
	def batch_exporter(self):
		return self.__batch_exporter

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
		return sorted(set(
			ls.to_children(
				obj, False,
				from_shape_transforms=True, keep_source_objects=False
			)
		), key=ls.long_item_name)

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
		The list of entire hierarchy of exported objects.
		I.e., specified objects with their children, grand-children etc.

		Shapes not included in the result. If shapes were given as <objects>,
		they're turned to their transforms (with other children).

		:param transforms_only:
			When True, only exported transforms (not their shapes) are returned.
		:param keep_order:
			Leave it to false if the order doesn't matter. It will work faster.
			When False, the processed objects are sorted alphabetically.
		:return: <list of PyNodes>
		"""
		objects = self._objects
		kw_args = dict(
			from_shape_transforms=True,
			keep_shapes=not transforms_only
		)
		if keep_order:
			return ls.to_hierarchy(objects, False, remove_duplicates=True, **kw_args)
		return sorted(set(
			ls.to_hierarchy(objects, False, remove_duplicates=False, **kw_args)
		), key=ls.long_item_name)

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
				ls.short_item_name(x) in _maya_default_objects
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

	def uv_sets_cleanup(self, kept_sets_rule=None):
		"""
		Cleans up UV-sets on the meshes selected for export.
			* ensures the 1st set is named "map1".
			* Removes all the extra sets, which don't match to the <kept_sets_rule> definition.

		:param kept_sets_rule: e.g.: (1, ('LM_out', 'LM'), 'windUVs', 'arrayID')
		"""
		if kept_sets_rule is None:
			kept_sets_rule = (1, ('LM_color', 'LM_out', 'LM'), 'windUVs', 'arrayID')
		if not kept_sets_rule:
			return self

		exported = self.get_all_exported_objects(False)
		if not exported:
			return self
		cleaner = cl.UVSets(exported, False, kept_sets_rule=kept_sets_rule)
		cleaner.rename_first_set()
		cleaner.remove_extra_sets()
		return self

	def uvs_sew(self, resolution=2048, pixel_fraction=0.6, uv_set=1):
		cl.UVs(
			self.get_all_exported_objects(transforms_only=True),
			selection_if_none=False, hierarchy=False,
			uv_set=uv_set
		).sew_extra_seams(resolution, pixel_fraction)
		return self

	@staticmethod
	def render_layers_cleanup():
		"""
		* Switches current render-layer back to default one.
		* Removes any other render-layers.
		"""
		pm_rl = pm.nt.RenderLayer
		def_lr = pm_rl.defaultRenderLayer()
		assert isinstance(def_lr, pm_rl)
		def_lr.setCurrent()
		extra_lrs = [
			lr for lr in pm.ls(exactType="renderLayer")
			if lr != def_lr
		]
		if extra_lrs:
			pm.delete(extra_lrs)

	def _color_sets_cleanup(self, match_kept_colors_f=None):
		"""
		Removes color sets for any object that don't match to the given rule.

		:param match_kept_colors_f:
			<function with 1 argument> the rule,
			returning True if the object needs it's color set to be kept.
				* the checked object (PyNode, Transform) is passed as the argument.
		"""
		from drl.for_maya.geo.components import color_sets as cs
		if match_kept_colors_f is None:
			return
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

	@staticmethod
	def _del_object_sets():
		cl.del_all_object_sets()

	@staticmethod
	def _del_unused_nodes():
		cl.del_unused_nodes()

	def _combine_child_groups(self, ends_with='_islanddn', matching_f=None):
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

		def _cleanup_combined(nu_comb):
			geo.freeze_transform(nu_comb, False)
			pm.delete(nu_comb, ch=1)
			return geo.reset_pivot(nu_comb, False)

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
			combined_group = err.WrongTypeError(combined_group, _t_transform, 'child_group').raise_if_needed()
			children = BaseExport.children(combined_group)

			if not children:
				if pm.listRelatives(combined_group, shapes=1):
					# no children BUT the transform itself is a geo-object (has shape)
					return _cleanup_combined(combined_group)
				return list()

			name = ls.short_item_name(combined_group)

			if len(children) == 1:
				# no need to combine, just cleanup move a single child up in hierarchy
				# extra-freeze - to prevent creating a scale-parent:
				combined = geo.freeze_transform(children[0], False)
			else:
				# we're processing the full-case: multiple children that needs to be combined:
				combined = pm.polyUnite(children, ch=0, mergeUVSets=1)[0]

			# in both cases above, the resulting object is still
			# in the wrong place in hierarchy, so we need to re-parent it under exported group:
			combined = pm.parent(combined, parent, absolute=1)[0]

			# final cleanup:
			combined = _cleanup_combined(combined)[0]
			try:
				# the old combined-group may have left.
				# So, before renaming the resulting object, we need to "free some space":
				pm.delete(combined_group)
			except pm.MayaNodeError:
				# the combined-group is already removed as history, in _cleanup_combined
				pass

			combined = pm.rename(combined, name)
			return [combined]


		def _process_single_group(group):
			"""
			Combine all the matching child groups (IslandDn) for the given parent group (Island itself).
			:param group: parent transform (Island group)
			:return: list of combined objects
			"""
			group = err.WrongTypeError(group, _t_transform, 'group').raise_if_needed()
			children = BaseExport.children(group)
			to_combine = [c for c in children if matching_f(c)]
			to_combine = geo.instance_to_object(to_combine, False)
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

		:param overwrite:
			<int>, whether existing file is overwritten:
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
			<bool>

			For deformed objects, tells to remove only the part of history
			that occur before the deformers.
				*
					When **False** (default), all the non-deformer modeling history is removed.
					No matter if it's before or after deformers.
		"""
		objects = self.get_all_exported_objects()
		cl.history.delete_smart(objects, False, before_deformers_only)
		return self

	def un_turtle(self):
		from drl.for_maya.plugins import Plugin
		ttl = Plugin('Turtle')
		if ttl.registered() and ttl.loaded():
			ttl.unload(remove_dependent_nodes=True)
		return self

	def mat_faces_to_obj(self):
		objects = self.get_all_exported_objects()
		cl.materials.all_faces_to_shape(objects, False)
		return self
