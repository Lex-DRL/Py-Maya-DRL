__author__ = 'Lex Darlog (DRL)'

from drl_common import errors as _err

from drl.for_maya import py_node_types as _pnt
_shape_poly_nurbs = (_pnt.shape.poly, _pnt.shape.nurbs)
_face_poly_nurbs = (_pnt.comp.poly.face, _pnt.comp.nurbs.face)
_t_sg = _pnt.sg


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
			val, _shape_poly_nurbs, var_name, 'poly- / NURBS-shape'
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
			val, _face_poly_nurbs, var_name, 'poly- / NURBS-face'
		)


class NotSG(UnsupportedItemBaseError):
	"""
	The given item is not an SG node.
	"""
	def __init__(self, val, var_name=None):
		super(NotSG, self).__init__(
			val, _t_sg, var_name
		)