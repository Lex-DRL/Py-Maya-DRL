__author__ = 'DRL'

from maya import cmds


from drl_common.py_2_3 import (
	str_t as _str_t,
	str_h as _str_h,
)

_t_base_iterable_or_str = tuple(list(_str_t) + [list, tuple])


class Node(object):
	def __init__(self, node=''):
		super(Node, self).__init__()
		if not isinstance(node, _str_t):
			raise Exception('<node> argument is of wrong type (string expected)')
		if not node:
			raise Exception('<node> argument is empty string')
		self.__full_path = ''
		self.name = node

	@property
	def name(self):
		paths = cmds.ls(self.__full_path)
		if not paths:
			raise Exception("Given node doesn't exist anymore: " + self.__full_path)
		return paths[0]
	@name.setter
	def name(self, value):
		if isinstance(value, Node):
			self.__full_path = value.full_path
			return
		if not isinstance(value, _t_base_iterable_or_str):
			raise Exception('Node name(s) expected. Provided: ' + repr(value))
		long_paths = cmds.ls(value, long=True)
		if not (long_paths and cmds.objExists(value)):
			raise Exception("Given node doesn't exist: " + repr(value))
		self.__full_path = long_paths[0]

	@property
	def full_path(self):
		return self.__full_path

	def type(self):
		return cmds.nodeType(self.full_path)

	def exists(self):
		return cmds.objExists(self.full_path)



class Attribute(object):
	def __init__(self, node=None, attrib_name=''):
		super(Attribute, self).__init__()
		if not isinstance(attrib_name, _str_t):
			raise Exception('<attrib_name> argument is of wrong type (string expected)')
		if not attrib_name:
			raise Exception('<attrib_name> argument is empty string')

		self.__node = Node(node)
		self.attrib_name = attrib_name

	@property
	def node(self):
		return self.__node
	@node.setter
	def node(self, value):
		self.__node = Node(value)

	@property
	def attrib_name(self):
		return self.__attr
	@attrib_name.setter
	def attrib_name(self, value):
		self.__attr = value

	@property
	def attrib_path(self):
		return self.node.name + '.' + self.attrib_name

	@property
	def attrib_full_path(self):
		return self.node.full_path + '.' + self.attrib_name

	@property
	def value(self):
		return cmds.getAttr(self.attrib_name)
	@value.setter
	def value(self, value):
		kwargs = dict()
		if self.type() is 'string':
			kwargs['type'] = 'string'
		cmds.setAttr(self.attrib_name, value, **kwargs)

	def type(self):
		return cmds.getAttr(self.attrib_full_path, type=True)