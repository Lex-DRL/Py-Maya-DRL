__author__ = 'DRL'

import pymel.core as _pm

sg = _pm.nt.ShadingEngine

transform = _pm.nt.Transform
shape = _pm.nt.Shape
shape_poly = _pm.nt.Mesh
shape_NURBS = _pm.nt.NurbsSurface
comp = _pm.Component
face_poly = _pm.MeshFace
face_NURBS = _pm.NurbsSurfaceFace

restricted_geo_types = (
	transform,
	shape,
	face_poly,
	face_NURBS
)
