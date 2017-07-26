__author__ = 'DRL'

import pymel.core as __pm

sg = __pm.nt.ShadingEngine

transform = __pm.nt.Transform

light_shape = __pm.nt.Light
cam_shape = __pm.nt.Camera

surf_shape = __pm.nt.SurfaceShape
geo_shape = __pm.nt.GeometryShape

shape = __pm.nt.Shape
shape_poly = __pm.nt.Mesh
shape_NURBS = __pm.nt.NurbsSurface

comp = __pm.Component

p_f = poly_face = __pm.MeshFace
p_v = poly_vertex = __pm.MeshVertex
p_vf = poly_vertex_face = __pm.MeshVertexFace
p_e = poly_edge = __pm.MeshEdge
p_uv = poly_uv = __pm.MeshUV

NURBS_face = __pm.NurbsSurfaceFace