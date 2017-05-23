__author__ = 'DRL'

from drl.for_maya.auto import cleanup as _cl
reload(_cl)


def all():
	return _cl.cleanup_all()


def skip_uvs():
	return _cl.cleanup_all(uv_sets_rename_first=False, uv_sets_remove_extra=False)


def skip_shapes():
	return _cl.cleanup_all(rename_shapes=False)


def create_normals_layer():
	return _cl.create_debug_normals_layer_if_needed()