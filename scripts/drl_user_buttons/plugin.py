__author__ = 'DRL'

from drl_common.py_2_3 import reload
from drl.for_maya import plugins as _p
reload(_p)


def un_turtle():
	_p.Plugin('Turtle').unload(remove_dependent_nodes=True)