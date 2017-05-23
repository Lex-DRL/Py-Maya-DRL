__author__ = 'DRL'

from drl import aivik as _avk
reload(_avk)


def update_duplicated_meshes():
	return _avk.update_duplicated.meshes()


def update_duplicated_with_offset():
	return _avk.update_duplicated.meshes_and_transforms()