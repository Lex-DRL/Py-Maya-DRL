__author__ = 'DRL'


from pymel import core as pm

from drl.for_maya import ui
from drl.for_maya.ls import pymel as ls
from drl.for_maya.ls.convert import components as comp

from drl_common import errors as err


def get_colors_on_vertexfaces(items=None, selection_if_none=True):
	"""
	Queries a list of vertex-face colors.

	:param items: source objects/components (will be converted to vertex faces if needed).
	:param selection_if_none: whether to use selection when no items given.
	:return: <list> of tuples: (MeshVertexFace, red, green, blue, alpha).
	"""
	items = ls.default_input.handle_input(items, selection_if_none)
	vfs = comp.convert_poly(items, selection_if_none=False, tvf=True, flatten=True)
	return [
		tuple(
			[vf] + pm.polyColorPerVertex(vf, q=1, r=1, g=1, b=1, a=1)
		) for vf in vfs
	]


def __get_color_comp_arg(arg):
	"""
	Makes sure the given argument is one of:

	* int/float - for exact match
	* tuple of exactly 2 float/int values - for match with range
	* None - for always match
	"""
	if arg is None:
		return None

	if isinstance(arg, (int, float)):
		return arg
	if isinstance(arg, list):
		arg = tuple(arg)

	if isinstance(arg, tuple):
		if len(arg) == 2:
			err.WrongTypeError(arg[0], (int, float), 'min range value', 'int or float').raise_if_needed()
			err.WrongTypeError(arg[1], (int, float), 'max range value', 'int or float').raise_if_needed()
			return arg
		raise IndexError('Exactly 2 items should be in the provided tuple for range. Got: ' + str(arg))

	raise err.WrongTypeError(arg, types_name='float, int, tuple of 2 ints or None')


def __error_check_color_args(*args):
	if len(args) == 0:
		return
	args = [__get_color_comp_arg(x) for x in args]
	if len(args) == 1:
		return args[0]
	return tuple(args)


def match_color_component(value, arg):
	"""
	Checks whether the given color-component (r/g/b/a) value matches the given argument.

	The argument is one of:

	* int/float - for exact match
	* tuple of exactly 2 float/int values - for match with range
	* None - for always match

	:return: bool
	"""
	if arg is None:
		return True
	if isinstance(arg, (int, float)):
		return value == arg
	# the range mode:
	return arg[0] <= value <= arg[1]


def _is_color_match(color, r=None, g=None, b=None, a=None):
	"""
	Checks whether the given color has the specified r/g/b/a values.

	Where r/g/b/a is one of:

	* int/float - for exact match
	* tuple of exactly 2 float/int values - for match within range
	* None - any value for this component (we don't care / always match)

	:return: True if all components match and False if at least one of them isn't in the given range.
	"""
	return all(
		map(match_color_component, color, [r, g, b, a])
	)


def get_vertex_faces_with_color(
	items=None, r=None, g=None, b=None, a=None, selection_if_none=True,
	show_progress=True, progress_title='Vertex-faces with color...', progress_message='Vertex-face: {0} / {1}'
):
	"""
	Queries the list of vertex-faces with the given color.

	The r/g/b/a arguments is one of:

	* int/float - for exact match
	* tuple of exactly 2 float/int values - for match with range
	* None - any value for this color component (we don't care / always match)

	:param items: source objects/components (will be converted to vertex faces before the check).
	:param selection_if_none: whether to use selection when no items given.
	:param show_progress: <bool> when True, an interactive ProgressWindow will be shown, allowing you to interrupt the operation.
	:param progress_title: <string> in show_progress mode, defines the ProgressWindow name.
	:param progress_message: <string> in show_progress mode, defines the message that will be formatted with current/total number of items.
	:return: flattened list of <MeshVertexFace>
	"""
	items = ls.default_input.handle_input(items, selection_if_none)
	if not items:
		return []

	r, g, b, a = __error_check_color_args(r, g, b, a)

	vf_colors = get_colors_on_vertexfaces(items, selection_if_none=False)

	num = len(vf_colors)
	if num == 0:
		return []

	if not show_progress:
		return [vfc[0] for vfc in vf_colors if _is_color_match(vfc[1:], r, g, b, a)]

	def _do_func(el, i, res):
		# assert isinstance(res, list)
		if _is_color_match(el[1:], r, g, b, a):
			res.append(el[0])

	return ui.ProgressWindow.do_with_each(
		vf_colors, _do_func, progress_title, progress_message
	)


def _comp_matches(component, matching_vertex_faces, vf_match_combine_f):
	# list of current component's vertex faces:
	vfs = comp.convert_poly(component, selection_if_none=False, tvf=True, flatten=True)
	# list of bool, which VFs are in the matching list:
	vfs_in_match = [(vf in matching_vertex_faces) for vf in vfs]
	# combining vertexFace-match to the main component match:
	return vf_match_combine_f(vfs_in_match)


def __get_components_with_matching_vertex_faces(
	matching_vertex_faces, items, inclusive=False,
	convert_to_comp_f=None,
	show_progress=True, progress_title='Filter components with color...', progress_message='Component: {0} / {1}'
):
	if not (items and matching_vertex_faces):
		return []
	vf_match_to_comp = any if inclusive else all

	conv_items = convert_to_comp_f(items)

	if not show_progress:
		return [
			c for c in conv_items
			if _comp_matches(c, matching_vertex_faces, vf_match_to_comp)
		]

	def _do_func(el, i, res):
		# assert isinstance(res, list)
		if _comp_matches(el, matching_vertex_faces, vf_match_to_comp):
			res.append(el)

	return ui.ProgressWindow.do_with_each(
		conv_items, _do_func, progress_title, progress_message
	)


def __get_component_with_color(
	items=None, r=None, g=None, b=None, a=None, inclusive=False, selection_if_none=True,
	convert_to_comp_f=None,
	show_progress=True, progress_title='components with color...', progress_message='-comp: {0} / {1}'
):
	"""
	Wrapper function for:

	* get_vertices_with_color
	* get_faces_with_color
	"""
	items = ls.default_input.handle_input(items, selection_if_none)
	len_i = len(items)
	if len_i == 0:
		return []

	r, g, b, a = __error_check_color_args(r, g, b, a)
	res = list()
	total_steps = len_i * 2
	cur_step = 0
	for i in items:
		item_name = i.name()
		cur_step += 1
		vfs_matching = get_vertex_faces_with_color(
			i, r, g, b, a, False,
			show_progress,
			'{0}/{1}: Get '.format(cur_step, total_steps) + progress_title,
			item_name + '-[VF]: {0}/{1}'
		)
		cur_step += 1
		res += __get_components_with_matching_vertex_faces(
			vfs_matching, i, inclusive, convert_to_comp_f,
			show_progress, '{0}/{1}: Filter '.format(cur_step, total_steps) + progress_title,
			item_name + progress_message
		)

	return res


def get_vertices_with_color(
	items=None, r=None, g=None, b=None, a=None, inclusive=False, selection_if_none=True,
	show_progress=True, progress_title='Vertices with color...', progress_message='Vertex: {0} / {1}'
):
	"""
	Queries the list of vertices with the given color.
	The check itself is actually performed per-vertex-face so there won't be any falsely
	added vertices which only got to the result due to the averaging of it's vertex faces.

	It's up to you to decide how vertex-face-match got converted to vertex-match, by <inclusive> argument (see below).

	The r/g/b/a arguments is one of:

	* int/float - for exact match
	* tuple of exactly 2 float/int values - for match with range
	* None - any value for this color component (we don't care / always match)

	:param items: source objects/components (will be converted to vertex faces before the check).
	:param inclusive: When on, the current vertex is considered matching if any of it's vertex-faces match. I.e., there also could be non-matching VFs. False by default, i.e. all VFs have to match.
	:param selection_if_none: whether to use selection when no items given.
	:param show_progress: <bool> when True, an interactive ProgressWindow will be shown, allowing you to interrupt the operation.
	:param progress_title: <string> in show_progress mode, defines the ProgressWindow name.
	:param progress_message: <string> in show_progress mode, defines the message that will be formatted with current/total number of items.
	:return: flattened list of <MeshVertex>
	"""
	return __get_component_with_color(
		items, r, g, b, a, inclusive, selection_if_none,
		lambda itms: comp.convert_poly(itms, selection_if_none=False, tv=True, flatten=True),
		show_progress, progress_title, progress_message
	)


def get_faces_with_color(
	items=None, r=None, g=None, b=None, a=None, inclusive=False, selection_if_none=True,
	show_progress=True, progress_title='Faces with color...', progress_message='Face: {0} / {1}'
):
	"""
	Queries the list of faces with the given color.
	The check itself is actually performed per-vertex-face so there won't be any falsely
	added faces which only got to the result due to the averaging of it's vertex faces.

	It's up to you to decide how vertex-face-match got converted to face-match, by <inclusive> argument (see below).

	The r/g/b/a arguments is one of:

	* int/float - for exact match
	* tuple of exactly 2 float/int values - for match with range
	* None - any value for this color component (we don't care / always match)

	:param items: source objects/components (will be converted to vertex faces before the check).
	:param inclusive: When on, the current vertex is considered matching if any of it's vertex-faces match. I.e., there also could be non-matching VFs. False by default, i.e. all VFs have to match.
	:param selection_if_none: whether to use selection when no items given.
	:param show_progress: <bool> when True, an interactive ProgressWindow will be shown, allowing you to interrupt the operation.
	:param progress_title: <string> in show_progress mode, defines the ProgressWindow name.
	:param progress_message: <string> in show_progress mode, defines the message that will be formatted with current/total number of items.
	:return: flattened list of <MeshFace>
	"""
	return __get_component_with_color(
		items, r, g, b, a, inclusive, selection_if_none,
		lambda itms: comp.convert_poly(itms, selection_if_none=False, tf=True, flatten=True),
		show_progress, progress_title, progress_message
	)


def get_components_with_color(
	items=None, r=None, g=None, b=None, a=None, selection_if_none=True,
	show_progress=True
):
	"""
	Queries the list of components with the given color.
	I's composed the most non-intersecting way possible. I.e.:

	* vertices added only if they're not already covered by matched polygons
	* vertex faces added only if they're not already covered by vertices

	The r/g/b/a arguments is one of:

	* int/float - for exact match
	* tuple of exactly 2 float/int values - for match with range
	* None - any value for this color component (we don't care / always match)

	:param items: source objects/components (will be converted to vertex faces before the check).
	:param selection_if_none: whether to use selection when no items given.
	:param show_progress: <bool> when True, an interactive ProgressWindow will be shown, allowing you to interrupt the operation.
	:return: flattened list of <MeshVertexFace>
	"""
	items = ls.default_input.handle_input(items, selection_if_none)
	if not items:
		return []
	r, g, b, a = __error_check_color_args(r, g, b, a)
	print '\n'

	def get_for_single_item(i, itm):
		"""
		The main code moved to this function, assuming it's evaluated independently
		for each item. It's done to speed up the search.
		:param itm:
		:return:
		"""
		seg_state = i * 4
		item_name = itm.name()  # it's already guaranteed to be a PyNode.
		vfs_matching = get_vertex_faces_with_color(
			itm, r, g, b, a, False, show_progress,
			'{0}/{1}: Get Vertex-Faces...'.format(seg_state + 1, total_progress_steps),
			item_name + '-[VF]: {0}/{1}'
		)
		if not vfs_matching:
			print (
				'No matching vertex faces found with color <{0}, {1}, {2}, {3}> for item: {4}'.format(
					r, g, b, a, itm
				)
			)
			return []

		faces = __get_components_with_matching_vertex_faces(
			vfs_matching, itm, False,
			lambda itms: comp.convert_poly(itms, selection_if_none=False, tf=True, flatten=True),
			show_progress,
			'{0}/{1}: Get Faces...'.format(seg_state + 2, total_progress_steps),
			item_name + '-[F]: {0}/{1}'
		)

		verts_match = __get_components_with_matching_vertex_faces(
			vfs_matching, itm, False,
			lambda itms: comp.convert_poly(itms, selection_if_none=False, tv=True, flatten=True),
			show_progress,
			'{0}/{1}: Get Vertices...'.format(seg_state + 3, total_progress_steps),
			item_name + '-[V]: {0}/{1}'
		)
		verts = [
			v for v in verts_match
			if not all(
				[
					(x in faces)
					for x in comp.convert_poly(v, False, tf=True, flatten=True)
				]
			)
		]

		def _filter_vertex_faces(matching_vfs):
			def _check_vertex_face(vert_face):
				return not (
					(comp.convert_poly(vert_face, False, tf=True, flatten=True)[0] in faces) or
					(comp.convert_poly(vert_face, False, tv=True, flatten=True)[0] in verts)
				)
			if not show_progress:
				return [
					vf for vf in matching_vfs
					if _check_vertex_face(vf)
				]

			def _do_func(el, i, res):
				# assert isinstance(res, list)
				if _check_vertex_face(el):
					res.append(el)

			return ui.ProgressWindow.do_with_each(
				matching_vfs, _do_func,
				'{0}/{1}: Filter Vertex Faces...'.format(seg_state + 4, total_progress_steps),
				item_name + '-[VF]: {0}/{1}'
			)

		vert_faces = _filter_vertex_faces(vfs_matching)

		print (
			'Found matching components with color <{0}, {1}, {2}, {3}> for item: {4}'.format(
				r, g, b, a, itm
			)
		)
		return faces + verts + vert_faces

	res = []
	total_progress_steps = len(items) * 4
	for idx, el in enumerate(items):
		res += get_for_single_item(idx, el)

	return res