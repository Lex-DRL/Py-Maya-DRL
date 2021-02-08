__author__ = 'DRL'

from drl_common.py_2_3 import reload
from drl.for_maya.plugins import uv_layout as _uvl
reload(_uvl)


def prepare():
	return _uvl.prepare_duplicates()


def transfer():
	return _uvl.transfer_from_duplicates()


def delete_tmp():
	return _uvl.delete_temp_duplicates()