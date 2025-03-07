__author__ = 'Lex Darlog (DRL)'

from functools import partial as _part
from pymel import core as _pm
from drl_common.utils import group_items as _group_items
from drl.for_maya.base_class import PolyItemsProcessorBase as __BaseProcessor

try:
	# support type hints in Python 3:
	import typing as _t
except ImportError:
	pass
from drl_py23 import (
	str_t as _str_t,
	str_h as _str_h,
)

_flatten_f = _part(_pm.ls, fl=1)


def __get_vf_id_single_shape(vertex_face, dimension_id=0):
	"""
	Gets the id of either vertex or face this vertex-face belongs to.

	:param dimension_id:
		* 0 - vertex
		* 1 - face
	:return: id of a vertex/face
	"""
	res = vertex_face.currentItemIndex()[dimension_id]  # type: int
	return res


def __get_vf_id_multi_shape(vertex_face, dimension_id=0):
	"""
	Gets the id of either vertex or face this vertex-face belongs to.

	:param dimension_id:
		* 0 - vertex
		* 1 - face
	:return:
		String ID, like: "pSphereShape1.1"

		Where number after dot is an id of a vertex/face.
	"""
	vf_id = vertex_face.currentItemIndex()[dimension_id]
	res = vertex_face.node().name() + '.' + str(vf_id)  # type: _str_h
	return res


def __vfs_grouped(vertex_faces_list, single_shape=False, dimension_id=0):
	"""
	Takes a flat list/iterable of vertex faces (i.e., no [20:50]),
	as PyNodes (not strings).

	Returns them grouped either by the vertex or face (depending on <dimension_id> arg).

	:param single_shape:
		Set to True, if the input is guaranteed to belong to a single shape.
		It will work a little faster.
	:param dimension_id:
		Group by:
			* 0 - vertex
			* 1 - face
	"""
	def get_id_single(vf):
		return __get_vf_id_single_shape(vf, dimension_id)

	def get_id_multi(vf):
		return __get_vf_id_multi_shape(vf, dimension_id)

	res = _group_items(
		vertex_faces_list,
		key_f=get_id_single if single_shape else get_id_multi
	)  # type: _t.List[_t.Tuple[_pm.MeshVertexFace, ...]]
	return res


def vfs_grouped_by_vertex(vertex_faces_list, single_shape=False):
	"""
	Takes a flat list of vertex faces.
	Returns them grouped by the **vertex** they belong to, as a list of tuples.

	:param vertex_faces_list:
		<Flattened list/iterable of PyNode vertex-faces>

		If you're unsure about any requirements, use the
		similar method from PolyCompConverter class.
		I.e., if you're not sure that:

		* an iterable of items is given (not a single item, not a dict)
		* it is flattened (i.e., no [25:50] items)
		* every item is a PyNode vertex face (not just a string).
	:param single_shape:
		<bool>

		Set to True, if the input is guaranteed to belong to a single shape.
		It will work a little faster.
	:return: <list of tuples>
	"""
	return __vfs_grouped(vertex_faces_list, single_shape, 0)  # 0 = vertex


def vfs_grouped_by_face(vertex_faces_list, single_shape=False):
	"""
	Takes a flat list of vertex faces.
	Returns them grouped by the **face** they belong to, as a list of tuples.

	:param vertex_faces_list:
		<Flattened list/iterable of PyNode vertex-faces>

		If you're unsure about any requirements, use the
		similar method from PolyCompConverter class.
		I.e., if you're not sure that:

		* an iterable of items is given (not a single item, not a dict)
		* it is flattened (i.e., no [25:50] items)
		* every item is a PyNode vertex face (not just a string).
	:param single_shape:
		<bool>

		Set to True, if the input is guaranteed to belong to a single shape.
		It will work a little faster.
	:return: <list of tuples>
	"""
	return __vfs_grouped(vertex_faces_list, single_shape, 1)  # 1 = face


class PolyCompConverter(__BaseProcessor):
	"""
	Poly components conversion class
	and also the base class for all the per-component poly processors.
	It provides the methods converting the items list to a specified component type.

	It respects inherited <hierarchy> argument.
	"""

	def convert(
		self,
		border=False, bo=False,
		from_edge=False, fe=False,
		from_face=False, ff=False,
		from_uv=False, fuv=False,
		from_vertex=False, fv=False,
		from_vertex_face=False, fvf=False,
		internal=False,
		to_edge=False, te=False,
		to_face=False, tf=False,
		to_uv=False, tuv=False,
		to_vertex=False, tv=False,
		to_vertex_face=False, tvf=False,
		flatten=False, fl=False
	):
		"""
		This is just a high-level wrapper to the polyListComponentConversion.

		:param border: (bo) <bool>

			Indicates that the converted components must be on the border of the selection.
			If it is not provided, the converted components will be the related ones.
			Flag can have multiple arguments, passed either as a tuple or a list.
		:param internal: <bool>

			Indicates that the converted components must be totally envolved
			by the source components.
			E.g. a converted face must have all of its surrounding vertices being given.
			If it is not provided, the converted components will be the related ones.
		:param flatten: (fl) <bool>

			Flattens the returned list of objects so that each component
			is identified individually.
		:return: <list> of corresponding components

		Additionally to the listed above, there are following arguments:

		from_*:
			Indicates the component type to convert from.

			If none of them is provided, it is assumed to be all of them,
			including poly objects.

		to_*:
			Indicates the component type to convert to.

			If none of them is provided, it is assumed to the object.

		... where * is one of the following or corresponding shorthands:
			* edge
			* face
			* uv
			* vertex
			* vertex_face
		"""
		if self.hierarchy:
			items = self.get_geo_items()
		else:
			items = self.items

		if not items:
			res = list()  # type: _t.List[_pm.Component]
			return res

		keys_values = dict(
			border=border or bo,
			fromEdge=from_edge or fe,
			fromFace=from_face or ff,
			fromUV=from_uv or fuv,
			fromVertex=from_vertex or fv,
			fromVertexFace=from_vertex_face or fvf,
			internal=internal,
			toEdge=to_edge or te,
			toFace=to_face or tf,
			toUV=to_uv or tuv,
			toVertex=to_vertex or tv,
			toVertexFace=to_vertex_face or tvf
		)

		kw_args = {
			kw: True
			for kw, v in keys_values.items()
			if v
		}

		res = _pm.polyListComponentConversion(items, **kw_args)  # type: _t.List[_pm.Component]

		if not res:
			res = list()  # type: _t.List[_pm.Component]
			return res

		if flatten or fl:
			# it's already guaranteed to be PyNodes
			res = _flatten_f(res)  # type: _t.List[_pm.Component]

		if not isinstance(res[0], _pm.PyNode):
			# assume: if 1st isn't a PyNode - then all of them are
			res = map(_pm.PyNode, res)  # type: _t.List[_pm.Component]

		return res

	def to_edges(self, flatten=False, internal=False, border=False):
		res = self.convert(
			flatten=flatten, internal=internal, border=border,
			to_edge=True
		)  # type: _t.List[_pm.MeshEdge]
		return res

	def to_edges_on_uv_border(self, internal=False, include_geo_border=False):
		"""
		Extra method for getting a list of border edges.

		It doesn't have the <flatten> argument, because the result is always flattened.
		"""
		edges = self.convert(
			flatten=True, internal=internal,
			to_edge=True
		)  # type: _t.List[_pm.MeshEdge]
		if not edges:
			res_empty = list()  # type: _t.List[_pm.MeshEdge]
			return res_empty

		to_edge_uvs_f = _part(_pm.polyListComponentConversion, fromEdge=True, toUV=True)
		is_on_uv_border = lambda x: len(_flatten_f(to_edge_uvs_f(x))) > 2
		if include_geo_border:
			is_border_edge = lambda x: x.isOnBoundary() or is_on_uv_border(x)
		else:
			is_border_edge = is_on_uv_border

		res = [e for e in edges if is_border_edge(e)]  # type: _t.List[_pm.MeshEdge]
		return res

	def to_vertices(self, flatten=False, internal=False, border=False):
		res = self.convert(
			flatten=flatten, internal=internal, border=border,
			to_vertex=True
		)  # type: _t.List[_pm.MeshVertex]
		return res

	def to_vertex_faces(self, flatten=False, internal=False, border=False):
		res = self.convert(
			flatten=flatten, internal=internal, border=border,
			to_vertex_face=True
		)  # type: _t.List[_pm.MeshVertexFace]
		return res

	def to_vertex_faces_grouped_by_vertex(
		self, internal=False, border=False
	):
		"""
		Extra method.

		It not just converts the given items to vertex faces,
		but also groups them by **vertex**.

		If you're absolutely sure that the provided items is already
		a flattened list of PyNode vertex-faces, then you can use
		a faster **vfs_grouped_by_vertex()** function instead.
		"""
		vfs = self.to_vertex_faces(flatten=True, internal=internal, border=border)
		return vfs_grouped_by_vertex(vfs, single_shape=False)

	def to_vertex_faces_grouped_by_face(
		self, internal=False, border=False
	):
		"""
		Extra method.

		It not just converts the given items to vertex faces,
		but also groups them by **face**.

		If you're absolutely sure that the provided items is already
		a flattened list of PyNode vertex-faces, then you can use
		a faster **vfs_grouped_by_face()** function instead.
		"""
		vfs = self.to_vertex_faces(flatten=True, internal=internal, border=border)
		return vfs_grouped_by_face(vfs, single_shape=False)

	def to_faces(self, flatten=False, internal=False, border=False):
		res = self.convert(
			flatten=flatten, internal=internal, border=border,
			to_face=True
		)  # type: _t.List[_pm.MeshFace]
		return res

	def to_uvs(self, flatten=False, internal=False, border=False):
		res = self.convert(
			flatten=flatten, internal=internal, border=border,
			to_uv=True
		)  # type: _t.List[_pm.MeshUV]
		return res
