__author__ = 'DRL'


from pymel import core as pm
from drl_common.utils import flatten_gen as _flat

try:
	# support type hints in Python 3:
	import typing as _t
except ImportError:
	pass
from drl_common.py_2_3 import str_t, str_hint

try:
	_hint_item_single = _t.Union[str_hint, pm.PyNode]
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
		if isinstance(element, str_t):
			return pm.PyNode(element)
		try:
			return pm.PyNode(element)
		except:
			raise NotNodeError(element, "Can't create PyNode from element: {0}")

	res = map(make_py_mel, _flat(items))
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

	if isinstance(obj, (str, unicode)):
		obj = pm.PyNode(obj)
	assert isinstance(obj, pm.PyNode)
	return obj
