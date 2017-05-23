__author__ = 'DRL'

from pymel import core as _pm
from drl.for_maya.geo.components import mesh_colors as _mc
reload(_mc)

_range_1 = (0.95, 1.1)


def get_red(select=True):
	res = _mc.get_components_with_color(r=_range_1)
	if res and select:
		_pm.select(res, r=1)
	return res


def get_green(select=True):
	res = _mc.get_components_with_color(g=_range_1)
	if res and select:
		_pm.select(res, r=1)
	return res


def get_blue(select=True):
	res = _mc.get_components_with_color(b=_range_1)
	if res and select:
		_pm.select(res, r=1)
	return res


def get_alpha(select=True):
	res = _mc.get_components_with_color(a=_range_1)
	if res and select:
		_pm.select(res, r=1)
	return res

