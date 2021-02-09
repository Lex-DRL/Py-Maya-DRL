__author__ = 'Lex Darlog (DRL)'


from pymel import core as pm

try:
	# support type hints in Python 3:
	import typing as _t
except ImportError:
	pass
from drl_common.py_2_3 import (
	str_t as _str_t,
	str_hint as _str_h,
)
from collections import (
	Iterable as _Iterable,
	Iterator as _Iterator,
)

try:
	_hint_item_single = _t.Union[_str_h, pm.PyNode]
	_hint_item_mult = _t.Union[_hint_item_single, _t.Iterable[_hint_item_single]]

except:
	pass


class NotMayaObjectBaseError(ValueError):
	"""
	The base class for errors, representing wrong value expected to be a Maya object.
	"""
	def __init__(self, wrong_object, message_template="Not a Maya object: {0}"):
		msg = message_template.format(repr(wrong_object))
		super(NotMayaObjectBaseError, self).__init__(msg)
		self.wrong_object = wrong_object
		self.message_template = message_template


class NotNodeError(NotMayaObjectBaseError):
	"""
	The given value is not a Maya node (not it's name/path nor PyNode object).
	"""
	def __init__(self, node, message_template="Not a Maya node: {0}"):
		super(NotNodeError, self).__init__(node, message_template)


class NotComponentError(NotMayaObjectBaseError):
	"""
	The given value is not a Maya node (not it's name/path nor PyNode object).
	"""
	def __init__(self, node, message_template="Not a Maya geo component: {0}"):
		super(NotComponentError, self).__init__(node, message_template)


def _flatten_items_gen(items, bruteforce=True, keep_strings=True):
	"""
	A variation of the common flatten_gen().
	It's designed to keep PyNodes properly, not converting them to char sequences.
	"""
	if isinstance(items, pm.PyNode) or (
			keep_strings and isinstance(items, _str_t)
	):
		# kept string or a PyNode:
		yield items
		return

	if bruteforce:
		# we try to detect non-iterable by actually attempting to iterate over it:
		try:
			items = iter(items)
		except TypeError:
			yield items
			return
	else:
		# only those classes inherited from built-in iterable classes
		# are considered iterables:
		if not isinstance(items, (_Iterable, _Iterator)):
			yield items
			return

	# it is indeed an iterable:
	for el in items:
		for sub in _flatten_items_gen(el):
			yield sub


def handle_input(
	items=None,  # type: _t.Optional[_hint_item_mult]
	selection_if_none=True, flatten=False,
	**ls_sel_args
):
	"""
	Pre-processes input objects/components. Can get current selection if nothing
	is given as a first argument.

	It ensures the list of items is 1D list of PyNodes.
	I.e., it:
		* expands included sets/lists/tuples to the actual elements.
		* ensures eah element is PyNode object.
	"""
	if items is None or not items:
		if selection_if_none:
			items = pm.ls(sl=True, **ls_sel_args)
		else:
			res = []  # type: _t.List[pm.PyNode]
			return res

	def make_py_mel(element):
		if isinstance(element, pm.PyNode):
			return element
		if isinstance(element, _str_t):
			return pm.PyNode(element)
		try:
			return pm.PyNode(element)
		except:
			raise NotNodeError(element, "Can't create PyNode from element: {0}")

	res = map(make_py_mel, _flatten_items_gen(items))
	# now we're guaranteed to have a list of PyNodes in items

	if flatten:
		res = pm.ls(res, fl=1)
	return res


def handle_single_obj(obj=None, selection_if_none=True, show_errors=True, **ls_sel_args):
	if obj is None:
		if selection_if_none:
			obj = pm.ls(sl=True, **ls_sel_args)
		else:
			if show_errors:
				raise Exception("No object is provided and selection isn't used.")
			obj = []
		if not obj:
			if show_errors:
				raise Exception("No object selected.")
			obj = None
		return obj

	if isinstance(obj, set):
		obj = list(obj)
	if isinstance(obj, (list, tuple)):
		if not obj:
			if show_errors:
				raise Exception("Empty list is given. Single expected.")
			return None
		if len(obj) > 1 and show_errors:
			raise Exception("Single object expected. Multiple provided: " + repr(obj))
		obj = obj[0]

	if isinstance(obj, _str_t):
		obj = pm.PyNode(obj)
	assert isinstance(obj, pm.PyNode)
	return obj
