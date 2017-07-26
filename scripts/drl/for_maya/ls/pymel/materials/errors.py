__author__ = 'DRL'

from drl_common import errors as _err

from . import __shorthands as _sh


class UnsupportedItemBaseError(_err.WrongTypeError):
	"""
	The given item is of unsupported type.
	Base class, not intended to be raised, only for exception handling.
	"""
	def __init__(self, val, types=None, var_name=None, types_name=None):
		super(UnsupportedItemBaseError, self).__init__(
			val, types, var_name, types_name
		)


class UnsupportedShape(UnsupportedItemBaseError):
	"""
	The given item is a shape of unsupported type.
	Only poly- / NURBS-surfaces are expected.

	:param val: the given nt.Shape
	:param var_name: optional string containing the name of the checked variable (for easier debug).
	"""
	def __init__(self, val, var_name=None):
		super(UnsupportedShape, self).__init__(
			val, (_sh.shape_poly, _sh.shape_NURBS), var_name, 'poly- / NURBS-shape'
		)


class UnsupportedComponent(UnsupportedItemBaseError):
	"""
	The given item is a component of unsupported type.
	Only poly- / NURBS-faces are expected.

	:param val: the given component
	:param var_name: optional string containing the name of the checked variable (for easier debug).
	"""
	def __init__(self, val, var_name=None):
		super(UnsupportedComponent, self).__init__(
			val, (_sh.poly_face, _sh.NURBS_face), var_name, 'poly- / NURBS-face'
		)


class NotSG(UnsupportedItemBaseError):
	"""
	The given item is not an SG node.
	"""
	def __init__(self, val, var_name=None):
		super(NotSG, self).__init__(
			val, _sh.sg, var_name
		)