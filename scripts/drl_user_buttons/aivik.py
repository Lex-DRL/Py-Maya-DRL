__author__ = 'DRL'

from drl_common.py_2_3 import reload
from drl import aivik as _avk
reload(_avk)


def update_duplicated_meshes():
	return _avk.replace_shapes.from_many_sources()


def update_duplicated_with_offset():
	return _avk.replace_shapes.from_many_sources_with_offset()


def replace_shapes_with():
	return _avk.replace_shapes.source_to_targets()


def export_buildings(map1_res=2048, kept_colors_regexps=None):
	return _avk.export.Buildings(save_scene_warning=False).export(
		map1_res=map1_res, kept_colors_regexps=kept_colors_regexps
	)


def export_pve_islands(map1_res=2048):
	return _avk.export.IslandsPVE(save_scene_warning=False).export(
		map1_res=map1_res
	)
