__author__ = 'Lex Darlog (DRL)'

from pymel import core as _pm
from drl_py23 import reload
from drl.for_maya.geo.components import vertices as _vtx
reload(_vtx)


def snap_point_to_point(select=True):
	res = _vtx.snap_point_to_point(object_space=True)
	if res and select:
		_pm.select(res, r=1)
	return res
