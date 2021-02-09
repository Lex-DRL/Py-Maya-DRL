__author__ = 'Lex Darlog (DRL)'

from pymel import core as _pm

from drl.for_maya.ls import pymel as _ls
from drl_common import errors as _err

zeroTransforms_matrix = (
	1.0, 0.0, 0.0, 0.0,
	0.0, 1.0, 0.0, 0.0,
	0.0, 0.0, 1.0, 0.0,
	0.0, 0.0, 0.0, 1.0
)


def _error_check_matrix(matrix):
	matrix = _err.WrongTypeError(matrix, (list, tuple), 'matrix').raise_if_needed()
	num_el = len(matrix)
	nu_res = list()
	if num_el == 4:
		if not all(map(
			lambda el: len(el) == 4,
			matrix
		)):
			raise _err.WrongValueError(matrix, 'matrix', '4x4 matrix')
		map(nu_res.extend, matrix)
		return nu_res
	if num_el == 3:
		if not all(map(
			lambda el: len(el) == 3,
			matrix
		)):
			raise _err.WrongValueError(matrix, 'matrix', '3x3 matrix')
		map(nu_res.extend, matrix)
		return nu_res
	if num_el == 9 or num_el == 16:
		return matrix
	raise _err.WrongValueError(matrix, 'matrix', '16-elements list/tuple')



def matrix_get(objects=None, selection_if_none=True, world_space=False):
	"""
	Returns transformation matrix for the given object.

	:param objects: The object to query the matrix for.
	:param world_space:
		When on, world-space matrix is returned. Otherwise, it's in Object space
	:return:
		<list of tuples>

		4x4 matrices for each object,
		where each matrix is a tuple of 16 items in row order
	"""
	objects = _ls.to_objects(
		objects, selection_if_none, remove_duplicates=True
	)
	if not objects:
		return list()

	kw_args = dict()
	if world_space:
		kw_args['worldSpace'] = 1
	else:
		kw_args['objectSpace'] = 1
	return [tuple(t.getMatrix(**kw_args)) for t in objects]


def matrix_set(
	objects=None, selection_if_none=True, matrix=None,
	world_space=False, relative=False
):
	"""
	Transforms the given object with the given matrix.

	:param objects: The object to transform.
	:param matrix: 4x4 matrix as list of 16 items in row order
	:param world_space:
		When on, world-space matrix is applied. Otherwise, it's in Object space
	:param relative: Apply relative transformation. When off, it's absolute.
	:return: <list of nt.Transform> processed objects.
	"""
	objects = _ls.to_objects(
		objects, selection_if_none, remove_duplicates=True
	)
	if not objects:
		return list()

	if matrix is None:
		if relative:
			return list()
		matrix = zeroTransforms_matrix

	matrix = _error_check_matrix(matrix)

	kw_args = dict(
		matrix=matrix
	)
	if world_space:
		kw_args['worldSpace'] = 1
	else:
		kw_args['objectSpace'] = 1

	if relative:
		kw_args['relative'] = 1
	else:
		kw_args['absolute'] = 1
	_pm.xform(objects, **kw_args)
	return objects


def reset(objects=None, selection_if_none=True, world_space=False):
	"""
	Resets transforms for the given objects.
	It can either reset transforms in world or in object space.

	:param objects: Object to transform.
	:param world_space: Reset in world space. Use object space otherwise.
	"""
	objects = _ls.to_objects(
		objects, selection_if_none, remove_duplicates=True
	)
	if not objects:
		return
	matrix_set(objects, False, matrix=None, world_space=world_space)


def reset_pivot(objects=None, selection_if_none=True, world_space=False):
	"""
	Set objects' pivots to (0, 0, 0) either in world or local (object) space.

	:param objects:
	:param selection_if_none:
	:param world_space:
		<bool>
			* When True, pivots are set in world-space.
			* Object-space otherwise (default).
	:return: <list of nt.Transform> processed objects.
	"""
	objects = _ls.to_objects(
		objects, selection_if_none, remove_duplicates=True
	)
	if not objects:
		return list()

	kw_args = dict(
		pivots=(0, 0, 0),
		absolute=1
	)

	if world_space:
		kw_args['worldSpace'] = 1
	else:
		kw_args['objectSpace'] = 1
	_pm.xform(objects, **kw_args)
		# ^ it's the same as performing t.setPivots() for each object
	return objects