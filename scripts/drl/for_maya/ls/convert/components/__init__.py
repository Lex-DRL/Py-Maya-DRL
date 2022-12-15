__author__ = 'Lex Darlog (DRL)'

from pymel import core as pm

from .base_class import PolyCompConverter as Poly
from .base_class import vfs_grouped_by_vertex, vfs_grouped_by_face

from drl.for_maya.geo.components import uv_sets
from drl.for_maya import ui

from drl_common import errors as err
from drl_py23 import (
	xrange as _xrange,
	izip as _izip,
)


def _uv_shells_from_mesh(mesh, uv_set=None):
	"""
	Low-level function which returns UVs grouped by shell, as tuple of lists.

	:param mesh: source mesh to get UVs for
	:param uv_set:
		uv-set to check.

		* None or 0 for the current set,
		* name or number (starting from 1) to get the specific UV-set.
	:return: <tuple of lists>: res[uvShell][UV]
	"""
	err.WrongTypeError(mesh, pm.nt.Mesh, 'mesh').raise_if_needed()
	if not mesh:
		return ()

	if not uv_set is None:
		uv_set = uv_sets.get_set_name(mesh, uv_set)

	shell_ids, num_sets = mesh.getUvShellsIds(uv_set)
	res = tuple([list() for x in _xrange(num_sets)])

	for uv, shell_id in _izip(mesh.map[:], shell_ids):
		res[shell_id].append(uv)

	return res


def uv_shells(
	items=None, selection_if_none=True,
	extend_to_full_shell=True, uv_set=None, collapse=False
):
	"""
	High-level function, converting any given input (transforms/mesh-shapes/components)
	to a list of UV-shells.
	The result is tuples of lists, where 1st level is a group of a shell
	and the 2nd level is a UV.

	:param items:
		<list>

		Source elements (objects/components) of a scene to be converted.
	:param selection_if_none:
		<bool>

		whether to use current selection if items is None.
	:param extend_to_full_shell:
		<bool>

		When True, the result will contain the full UV-shells,
		even if just one UV was given as a source item.
		Otherwise, there will be only those UVs that were directly converted from items.
	:param uv_set:
		uv-set to check.

		* None or 0 for the current set,
		* name or number (starting from 1) to get the specific UV-set.

		WARNING! Though it's possible to specify a uv-set here, the function will work MUCH faster if just currently active UV-set is used.
	:param collapse:
		<bool>

		the opposite to flatten. Combines multiple MeshUV items to single range, if possible.
	:return: <tuple of lists>: res[uvShell][UV]
	"""
	from drl.for_maya.ls import pymel
	from drl_common import utils
	progress_window = ui.ProgressWindow

	# first, get a non-duplicating list of Mesh-shapes for the given/selected items:
	progress_window('Preparation...', 'Getting UV-shells', max=100)
	shapes = utils.remove_duplicates(
		pymel.to_shapes(items, selection_if_none, exact_type=pm.nt.Mesh)
	)

	if not shapes:
		progress_window.end()
		return tuple()

	for s in shapes:
		err.WrongTypeError(s, pm.nt.Mesh, 'shape').raise_if_needed()

	if not isinstance(extend_to_full_shell, bool):
		extend_to_full_shell = bool(extend_to_full_shell)

	# if necessary, remember currently active uv-set and switch it:
	prev_sets = list()
	do_change_set = not (
		uv_set is None or
		(isinstance(uv_set, int) and uv_set == 0)
	)
	if do_change_set:
		for s in shapes:
			uv_set_name = uv_sets.get_set_name(s, uv_set)
			cur_set = uv_sets.get_current(s)
			if cur_set == uv_set_name:
				cur_set = None
			else:
				uv_sets.set_current_for_singe_obj(s, uv_set_name)
			prev_sets.append((s, cur_set))

	# now, let's prepare current items converted to UVs.
	# Set is better then a list since order doesn't matter:
	all_uvs = set(
		Poly(items, selection_if_none).convert(to_uv=True, flatten=True)
	)

	progress_window.end()

	def _add_sets_from_single_shape(shape, all_uvs_set, out_res_list):
		all_cur_shells = _uv_shells_from_mesh(shape)  # UV-shells for current shape.
			# No need to pass a uv-set, since it's shape already active
			# So far, all uv-shells are returned,
			# as a next step we'll intersect it with a given items.

		cur_shells = list()
		for i, shell in enumerate(all_cur_shells):
			cur_shells.append(
				[uv for uv in shell if (uv in all_uvs_set)]  # only selected UVs kept
			)
			all_uvs_set -= set(shell)  # remove already added UVs for performance reasons

		# forget about shells we didn't select:
		if extend_to_full_shell:
			cur_shells = [all_cur_shells[i] for i, shell in enumerate(cur_shells) if shell]
		else:
			cur_shells = [x for x in cur_shells if x]

		if collapse:
			cur_shells = [
				Poly(uvs, False).convert(to_uv=True)
				for uvs in cur_shells
			]
		return out_res_list + cur_shells  # add the shells of this shape to the overall result

	# and finally, let's combine together all the UV-shells from different shapes,
	# keeping only those UVs which were related to the given items:
	res = list()
	num = len(shapes)
	progress_window('Shape: 0 / %s' % num, 'Getting UV-shells', max=num)
	i = 0
	while progress_window.is_active():
		s = shapes[i]
		progress_window.message = 'Shape: {0} / {1}'.format(i + 1, num)
		res = _add_sets_from_single_shape(s, all_uvs, res)
		i += 1
		progress_window.increment()

	if do_change_set:
		for s, prev_set in prev_sets:
			if not prev_set is None:
				uv_sets.set_current_for_singe_obj(s, prev_set)

	return tuple(res)  # list to tuple, for performance reasons