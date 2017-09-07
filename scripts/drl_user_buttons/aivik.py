__author__ = 'DRL'

from drl import aivik as _avk
reload(_avk)


def update_duplicated_meshes():
	return _avk.replace_shapes.from_many_sources()


def update_duplicated_with_offset():
	return _avk.replace_shapes.from_many_sources_with_offset()


def export_buildings(map1_res=2048):
	return _avk.export.Buildings().export(map1_res=map1_res)


def export_pve_islands(map1_res=2048):
	return _avk.export.IslandsPVE().export(map1_res=map1_res)
