__author__ = 'Lex Darlog (DRL)'


from drl_py23 import reload
from drl.for_maya.hud import unity_vertex_count as _unity_count
reload(_unity_count)


unity_count_toggle = _unity_count.toggle
unity_count_enable = _unity_count.enable
unity_count_disable = _unity_count.disable