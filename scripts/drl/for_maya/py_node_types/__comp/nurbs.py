__author__ = 'Lex Darlog (DRL)'

import pymel.core as __pm

cv = control_vertex = __pm.NurbsSurfaceCV
ep = edit_point = __pm.NurbsSurfaceEP
f = face = __pm.NurbsSurfaceFace  # patch
iso = isoparm = __pm.NurbsSurfaceIsoparm  # surface point or isoparm

a_t = any_tuple = (cv, ep, f, iso)