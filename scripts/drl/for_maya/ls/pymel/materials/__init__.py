__author__ = 'DRL'

from itertools import izip as _i_zip

from .. import __common as _ls
from .. import default_input as _def

from drl.for_maya import base_classes as _bs
from drl_common import utils as _utils
from drl_common import errors as _err

from . import errors, sg_attr_names
_sg_a = sg_attr_names

from . import __shorthands as _sh

import pymel.core as _pm
_pm_ls = _pm.ls


def __sg_to_mat(
	sg, mat_type=_sg_a.MAT_SURF,
	fallback_from_mr=True, fallback_to_mr=False
):
	"""
	Convert a single SG to it's material.
	SG has to be a PyNode (nt.ShadingEngine), it already needs to be checked.

	:param sg: <nt.ShadingEngine>
	:param mat_type: <string> one of options from **sg_attr_names** sub-module.
	:param fallback_from_mr:
		<bool>

		Whether to check a default Maya material if a MR's one is queried
		and it's not connected.
	:param fallback_to_mr:
		<bool>

		The opposite: whether to fallback from Maya material to MR.
	:return:
		<PyNode / None>
			* A connected material if found.
			* None otherwise.
	"""
	def get_connected(attr_nm):
		print sg.attr(attr_nm).inputs()
		return sg.attr(attr_nm).inputs()

	connected = get_connected(mat_type)
	if connected:
		return connected[0]

	mat_type = _sg_a.fallback_conditionally(mat_type, fallback_from_mr, fallback_to_mr)
	if mat_type is None:
		return None

	connected = get_connected(mat_type)
	if connected:
		return connected[0]
	return None


def sg_to_mat(
	sg, mat_type=_sg_a.MAT_SURF,
	fallback_from_mr=True, fallback_to_mr=False
):
	"""
	Convert a single SG to it's material.

	:param sg: <nt.ShadingEngine>

		:raises NotSG: if wrong type
	:param mat_type: <string> one of options from **sg_attr_names** sub-module.
	:param fallback_from_mr:
		<bool>

		Whether to check a default Maya material if a MR's one is queried
		and it's not connected.
	:param fallback_to_mr:
		<bool>

		The opposite: whether to fallback from Maya material to MR.
	:return:
		<PyNode / None>
			* A connected material if found.
			* None otherwise.
	"""
	sg = _def.handle_input(sg, False, type=_sh.sg)
	if not sg:
		return None
	if len(sg) > 1:
		raise errors.NotSG(sg, 'sg')
	sg = sg[0]
	sg = errors.NotSG(sg, 'sg').raise_if_needed()

	if not mat_type:
		mat_type = _sg_a.MAT_SURF

	return __sg_to_mat(
		sg, mat_type, fallback_from_mr, fallback_to_mr
	)


def sgs_to_materials(
	sgs, mat_type=_sg_a.MAT_SURF, exclude_not_connected=True,
	fallback_from_mr=True, fallback_to_mr=False
):
	"""
	Convert one or multiple SGs to their materials.

	:param sgs: <list/string/nt.ShadingEngine> shading groups
	:param mat_type: <string> one of options from **sg_attr_names** sub-module.
	:param exclude_not_connected:
		<bool>

		If no material is found (even with fallbacks),
		whether to exclude **None** items from result.
			* **True** (default) - only actual materials are kept in the result.
			*
				**False** - keep **None** items for those SGs which don't have a material.
				This is useful if you want to match input list of SGs with their
				corresponding materials in the resulting list.

		**WARNING**: even when **False**, the input and resulting lists may not match
		if there was anything but SG in the input.
	:param fallback_from_mr:
		<bool>

		Whether to check a default Maya material if a MR's one is queried
		and it's not connected.
	:param fallback_to_mr:
		<bool>

		The opposite: whether to fallback from Maya material to MR.
	:return:
		<list of PyNode / None>
			* A connected materials.
			* None if nothing is connected (and **exclude_not_connected** = False).
	"""
	sgs = _def.handle_input(sgs, False, type=_sh.sg)
	if not mat_type:
		mat_type = _sg_a.MAT_SURF

	mats = [
		__sg_to_mat(sg, mat_type, fallback_from_mr, fallback_to_mr) for sg in sgs
	]
	if exclude_not_connected:
		mats = [m for m in mats if not(m is None)]
	return mats


def items_to_shapes(items, selection_if_none=False, keep_order=False):
	shapes = _ls.to_shapes(
		items, selection_if_none,
		any_geo=True, remove_duplicates=keep_order
	)
	if shapes and not keep_order:
		return _ls.sorted_items(shapes, False)
	return shapes


def _list_sgs_of_shape(shapes):
	"""
	List SGs assigned to the given shape.
	Multiple shapes could be given, but the result may contain duplicates then.

	:param shapes: <PyNode/iterable of them> Geo-Shapes
	:return: <list of nt.ShadingEngine> Assigned SGs.
	"""
	if not shapes:
		return list()
	res = _pm.listConnections(shapes, type=_sh.sg, s=0, d=1)
	return res if res else list()


def _list_sgs_of_multiple_shapes(shapes, keep_order=False):
	"""
	List SGs assigned to the given shapes.
	Unlike _list_sgs_of_shape(), the duplicates are removed from the result.

	:param shapes: <PyNode/iterable of them> Geo-Shapes
	:return: <list of nt.ShadingEngine> Assigned SGs.
	"""
	if not shapes:
		return list()
	res = _pm.listConnections(shapes, type=_sh.sg, s=0, d=1)
	if not res:
		return list()

	if keep_order:
		return _utils.remove_duplicates(res)
	return _ls.sorted_items(res, False)


# ---------------------------------------------------------


class AssignedTo(_bs.ItemsProcessorBase):
	"""
	Get SGs assigned to given poly-/NURBS- shapes or faces.
	"""
	def __init__(self, items=None, selection_if_none=True):
		super(AssignedTo, self).__init__(_sh.restricted_geo_types)
		self.set_items(items, selection_if_none)

	@staticmethod
	def __is_single_sg_on_all_shapes(sgs_for_each_shape):
		"""
		Checks whether all the shapes of the object share the same single SG.

		:param sgs_for_each_shape:
			<iterable of iterable-s of SGs>

			SGs for each shape. I.e.:

			[
				(SG1, SG2),  # SGs on shape1

				(SG2, SG3),  # SGs on shape2

				(SG1,)  # SGs on shape3
			]  # all SG# variables are PyNodes of SG (nt.ShadingEngine)
		:return: <bool>
		"""
		return all(
			# each shape has only one SG on it:
			map(
				lambda shape_sgs: len(shape_sgs) == 1,
				sgs_for_each_shape
			)
		) and len(
			# combined list of SGs on all object shapes:
			_utils.remove_duplicates([sgs[0].name() for sgs in sgs_for_each_shape])
		) == 1

	def _get_items_for_testing(self):
		"""
		Cleanup a list of items, where each item has exactly one SG assigned to it.

			* Empty transforms or not-expected components are filtered out.
			* Components are flattened
			*
				Transforms added if all of their shapes share the same single SG
				or have no SG at all

				*
					otherwise, they're flattened to shapes
					(which in turn could be flattened too)
			*
				Shapes added if they have a single SG assigned

				* otherwise, flattened to all the shape's faces

		:return: <list of PyNodes>, each item has a single SG assigned.
		"""
		items = self.items
		if not items:
			return list()
		items = _pm_ls(items, fl=1)

		res = list()  # list of items, each having only a single SG
		res_append = res.append
		res_extend = res.extend

		def _add_shape(shape, num_shape_sgs):
			"""
			Attach a single shape to the list of tested items.
			If it has single SG, the shape itself is added.
			Otherwise, all of it's faces.

			:param shape: mesh/NURBS shape node
			:param num_shape_sgs: number of shading groups applied to the shape
			"""
			if num_shape_sgs < 2:
				# a single or no SGs assigned to the shape
				res_append(shape)
				return

			# multiple shading groups connected, we need to test per-face:
			if isinstance(shape, _sh.shape_poly):
				res_extend(
					_pm_ls(shape.name() + '.f[*]', fl=1)
				)
				return
			if isinstance(shape, _sh.shape_NURBS):
				res_extend(
					_pm_ls(shape.name() + '.sf[*][*]', fl=1)
				)
				return

			# We shouldn't even get here because items are guaranteed to have
			# one of the shape types used above.
			# But just as a fail-safe:
			raise errors.UnsupportedShape(shape, 'shape')

		def _add_item(item):
			"""
			Attach a single geo-item (Transform/Shape/Face) to the list of tested items.

				* If a face is given, it's added flattened.
				*
					If a transform or shape is given, and a single SG is assigned to it,
					the node is attached to a list as is.
				* Otherwise, all the shape-faces added

			:param item: <PyNode> Transform, Shape, or a single face Component
			"""
			if isinstance(item, _sh.comp):
				# each component is guaranteed to be either poly- or NURBS-face,
				# so no need to test for specific component types
				res_extend(
					_pm_ls(item, fl=1)
				)
				return

			item_shapes = items_to_shapes(item)  # list of Shapes
			if not item_shapes:
				# skip a transform with no shapes
				return

			item_sgs_by_shape = [
				_list_sgs_of_shape(shp) for shp in item_shapes
			]  # list of lists, SGs of each corresponding shape

			# append transform/shape directly if all of it's shapes
			# have no SGs assigned:
			if not any(item_sgs_by_shape):
				res_append(item)
				return

			# append transform/shape directly if all of it's shapes
			# have the same single SG assigned directly to them (not to faces):
			if (
				# all the shapes of this node have the same single SG assigned:
				AssignedTo.__is_single_sg_on_all_shapes(item_sgs_by_shape)
			):
				sg = item_sgs_by_shape[0][0]
				sg_assigned_to = _pm.sets(sg, q=1)
				if all(map(  # and SG is assigned directly to the shape, not to it's faces
					lambda shape: (shape in sg_assigned_to),
					item_shapes
				)):
					res_append(item)
					return

			# add shapes one-by-one:
			for shp, sgs in _i_zip(item_shapes, item_sgs_by_shape):
				_add_shape(shp, len(sgs))

		for it in items:
			_add_item(it)

		return res

	def grouped_by_sg(self, collapse_faces=True):
		"""
		Group items by assigned Shading Group.
			*
				The transforms are left intact, if all their shapes either have no SG
				or the same single SG assigned to them directly (i.e., not to faces).

				Otherwise, Transforms are expanded to their shapes.
			*
				Shapes are left intact if they have a single SG assigned directly to them
				(not to their faces).

				Otherwise, Shapes are expanded to their faces.
			* Faces are flattened and grouped by SG one-by-one.

		:param collapse_faces:
			<bool>
				*
					When True (default), the resulting faces
					are collapsed back to their ranges. I.e., (5, 6, 7, ... 92) -> [5:92]
				* Otherwise, the faces in the result are flattened.
		:return:
			<tuple of tuples>:
				(
					(SG1, sg_items1),  # all the items using this shading group

					(SG2, sg_items2),

					...

					(None, items_with_no_sg)  # always present in the result
				)
		"""
		items = self._get_items_for_testing()
			# each item is one of:
			# * single transform/shape with a single SG assigned directly to it
			# * single poly- / NURBS-face

		if not items:
			return tuple()

		shapes = items_to_shapes(items)
		possible_shading_groups = _ls.sorted_items(_list_sgs_of_shape(shapes), False)
			# These are SGs assigned to shapes.
			# But since components could be provided as <items>,
			# we could get here SGs that aren't assigned to any given item.
			# Therefore, SGs are only "possible".
		del shapes
		sg_assigned_to = tuple([
			# A tuple of sets.
			# each item corresponds to SG (same as res)
			# and stores a set of flattened items this SG is assigned to.
			set() for x in possible_shading_groups + [False]
		])
		sg_groups = dict()  # remember which SG has which ID in the res tuple

		def _res_template_list():
			"""
			Generate a list template for <res>:
				[
					[SG1, []],  # SG and an empty list where assigned items will be added

					[SG2, []],

					...

					[False, []]  # items that have no SG assigned
				]

			During process, <sg_assigned_to> and <sg_groups> are updated.

			:return: <list of tuples>
			"""
			res_array = list()
			res_append = res_array.append

			for i, sg in enumerate(possible_shading_groups):
				res_append(
					[sg, list()]
				)
				assigned_to = _pm.sets(sg, q=1)
				if assigned_to:
					assigned_to = _pm_ls(assigned_to, fl=1)
				else:
					assigned_to = list()
				sg_assigned_to[i].update(assigned_to)
				sg_groups[sg.name()] = i
			sg_groups[False] = len(possible_shading_groups)
			res_append([None, list()])
			return res_array

		res = _res_template_list()

		def _find_assigned_sg(item):
			if isinstance(item, _sh.transform):
				# We can have Transform here only if it has shapes
				# and all of them share the same SG (or none), assigned directly
				# (to shape, not to faces).
				item = items_to_shapes(item)[0]
			if isinstance(item, _sh.shape):
				shape_sgs = _list_sgs_of_shape(item)
				if shape_sgs:
					return shape_sgs[0]
				return False
			item = _err.WrongTypeError(item, _sh.restricted_geo_types, 'item').raise_if_needed()
			for sg, assigned_to in _i_zip(possible_shading_groups, sg_assigned_to):
				if item in assigned_to:
					return sg
			return False

		for itm in items:
			assigned_sg = _find_assigned_sg(itm)
			if isinstance(assigned_sg, _sh.sg):
				assigned_sg = assigned_sg.name()
			sg_group = res[
				sg_groups[assigned_sg]
			][1]
			sg_group.append(itm)

		# done.
		# technically, we're now have generated the res.
		# the only thing left is collapsing and turning list to tuples.

		def _single_item_collapsed(sg, gr):
			sorted_gr = _ls.sorted_items(gr, False)
			return sg, _ls.un_flatten_components(sorted_gr, False)

		single_item_f = lambda sg, gr: (sg, gr)
		if collapse_faces:
			single_item_f = _single_item_collapsed

		res = tuple((
			single_item_f(sg, gr) for sg, gr in res
			if ((sg is None) or gr)
		))
		return res

	def shading_groups(self, per_face_check=True):
		"""
		Shading groups assigned to given items.

		:param per_face_check:
			<bool>

			*
				When **True** (default), the accurate check is performed.
				I.e., only those SGs returned that are assigned to the exactly given faces.
			*
				When **False**, the SGs detection performed simply by shape.
				So the result can contain extra SGs which aren't assigned to any
				of the given faces, but are just used by some other faces in the same mesh.

			Use **False** only as a performance optimization
			if you check reeeeally many components.
		:return: <tuple of PyNodes> Shading Groups (nt.ShadingEngine)
		"""
		if per_face_check:
			return tuple([
				sg for sg, items in self.grouped_by_sg()[:-1]
			])
		return tuple(_list_sgs_of_multiple_shapes(
			items_to_shapes(self.items)
		))