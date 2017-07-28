__author__ = 'DRL'

import pymel.core as __pm

sg = __pm.nt.ShadingEngine

transform = __pm.nt.Transform

lgt_shape = light_shape = __pm.nt.Light
cam_shape = camera_shape = __pm.nt.Camera

surf_shape = surface_shape = __pm.nt.SurfaceShape
geo_shape = geometry_shape = __pm.nt.GeometryShape

shape = __pm.nt.Shape
shape_poly = __pm.nt.Mesh
shape_nurbs = __pm.nt.NurbsSurface
shape_curve = __pm.nt.NurbsCurve

comp = component = __pm.Component

p_f = poly_face = __pm.MeshFace
p_v = poly_vertex = __pm.MeshVertex
p_vf = poly_vertex_face = __pm.MeshVertexFace
p_e = poly_edge = __pm.MeshEdge
p_uv = poly_uv = __pm.MeshUV

n_cv = nurbs_cv = __pm.NurbsSurfaceCV
n_ep = nurbs_ep = __pm.NurbsSurfaceEP
n_f = nurbs_face = __pm.NurbsSurfaceFace  # patch
n_iso = nurbs_isoparm = __pm.NurbsSurfaceIsoparm  # surface point or isoparm

c_cv = curve_cv = __pm.NurbsCurveCV
c_ep = curve_ep = __pm.NurbsCurveEP
c_p = curve_point = __pm.NurbsCurveParameter
