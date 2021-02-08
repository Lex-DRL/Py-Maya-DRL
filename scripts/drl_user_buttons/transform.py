__author__ = 'DRL'


from drl_common.py_2_3 import reload
from drl.for_maya import transformations as _tr
from drl.for_maya import geo as _g
reload(_tr)
reload(_g)


def reset_pivot():
	return _tr.reset_pivot()


def freeze_pivot():
	_g.freeze_pivot()