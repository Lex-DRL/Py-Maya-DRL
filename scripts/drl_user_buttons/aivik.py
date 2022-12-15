__author__ = 'Lex Darlog (DRL)'

from drl_py23 import reload
from drl import aivik as _avk
from drl.aivik import (
	replace_shapes as _replace_shapes,
	export as _export
)
reload(_avk)


def update_duplicated_meshes():
	return _replace_shapes.from_many_sources()


def update_duplicated_with_offset():
	return _replace_shapes.from_many_sources_with_offset()


def replace_shapes_with():
	return _replace_shapes.source_to_targets()


def export_buildings(map1_res=2048, kept_colors_regexps=None):
	return _export.Buildings(save_scene_warning=False).export(
		map1_res=map1_res, kept_colors_regexps=kept_colors_regexps
	)


def export_pve_islands(map1_res=2048):
	return _export.IslandsPVE(save_scene_warning=False).export(
		map1_res=map1_res
	)
