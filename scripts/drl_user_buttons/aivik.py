__author__ = 'DRL'

from drl import aivik as _avk
reload(_avk)


def update_duplicated_meshes():
	return _avk.update_duplicated.meshes()


def update_duplicated_with_offset():
	return _avk.update_duplicated.meshes_and_transforms()


def export_buildings(map1_res=2048):
	return _avk.export.Buildings().export(map1_res=map1_res)


def export_pve_islands(map1_res=2048):
	return _avk.export.IslandsPVE().export(map1_res=map1_res)
