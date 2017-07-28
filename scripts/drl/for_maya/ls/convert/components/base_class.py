__author__ = 'DRL'

from pymel import core as _pm

from drl.for_maya.base_class import ItemsProcessorBase as __BaseProcessor

from drl.for_maya import py_node_types as __pnt

# transform, poly shape and all the poly component types
_tt_poly_geo_all = tuple(
	[__pnt.transform, __pnt.shape.poly] +
	list(__pnt.comp.poly.any_tuple)
)


class PolyCompConverter(__BaseProcessor):
	"""
	Poly components conversion class
	and also the base class for all the per-component poly processors.
	It:
		* Overrides the constructor, specifying the allowed PyNode types for the input.
		* Provides the methods converting the items list to a specified component type.

	:param to_hierarchy:
		<bool> During all PolyConversions, how to convert transforms with children:
			* True - each Transform is converted to the components of the entire hierarchy.
			* False - only the "direct" children' components are in the result.
		It affects only transforms in the items list.
	"""
	def __init__(self, items=None, selection_if_none=True, to_hierarchy=False):
		super(PolyCompConverter, self).__init__(_tt_poly_geo_all)
		self.set_items(items, selection_if_none)
		self.to_hierarchy = bool(to_hierarchy)

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
		if self.to_hierarchy:
			items = self.get_geo_items(hierarchy=True)
		else:
			items = self.items

		if not items:
			return list()

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

		kw_args = dict()

		for kw, v in keys_values.iteritems():
			if v:
				kw_args[kw] = True

		res = _pm.polyListComponentConversion(items, **kw_args)

		if flatten or fl:
			res = _pm.ls(res, fl=1)

		return res

	def to_edges(self, flatten=False, internal=False, border=False):
		return self.convert(
			flatten=flatten, internal=internal, border=border,
			to_edge=True
		)

	def to_vertices(self, flatten=False, internal=False, border=False):
		return self.convert(
			flatten=flatten, internal=internal, border=border,
			to_vertex=True
		)

	def to_vertex_faces(self, flatten=False, internal=False, border=False):
		return self.convert(
			flatten=flatten, internal=internal, border=border,
			to_vertex_face=True
		)

	def to_faces(self, flatten=False, internal=False, border=False):
		return self.convert(
			flatten=flatten, internal=internal, border=border,
			to_face=True
		)

	def to_uvs(self, flatten=False, internal=False, border=False):
		return self.convert(
			flatten=flatten, internal=internal, border=border,
			to_uv=True
		)