__author__ = 'DRL'

import sys as __sys
from pymel import core as pm

from drl.for_maya.ls import pymel as ls
from drl.for_maya.geo.components import uv_sets
from drl.for_maya.base_class import PolyObjectsProcessorBase as __BaseProcessor
from drl_common import errors as err
from drl_common import utils

from drl.for_maya import py_node_types as _pnt
_t_shape_any = _pnt.shape.any

_this = __sys.modules[__name__]
_str_types = (str, unicode)
_rule_types = (int, float, str, unicode)


class UVSetsRule(object):
	"""
	This class instance describes a rule for keeping/removing UV-sets.
	The rule's syntax is simple. It's a tuple of possible UV-sets, where each UV-set
	could be represented as a fallback sequence. I.e.:

	(
		'WindUVs',
		('LM_out', 'LM'),
		1,
		0
	)

	It means: select WindUVs, the 1st, the current UV-set and also: (LM_out if exist, otherwise 'LM').

	:param rule: a tuple of possible sets. Each possible set is one of:

		* <string> uv-set name
		* <int> uv-set number:
			* 0 (or empty string) - current
			* positive - 1-based UV-set number
			* negative - 1-based UV-set number. counted from the end
		* <tuple of strings/ints> fallback sequence
		optionally, a single int/string/UVSetsRule could be passed
			* when UVSetsRule instance is passed, it's <is_keep> property overrides the next argument.
	:param is_keep: whether this rule describes kept or removed sets
	"""
	def __init__(self, rule, is_keep=True):
		super(UVSetsRule, self).__init__()
		self.__is_keep = bool(is_keep)
		self.__rule = tuple()
		self.__set_rule(rule)

	def __set_rule(self, rule):
		if isinstance(rule, UVSetsRule):
			# create a new instance from the given:
			self.__rule = rule.rule
			self.__is_keep = rule.is_keep
			return

		def _single(val):
			# process a single-value rule (string/float/int)
			if isinstance(val, float):
				val = int(val)
			val = (val,)
			return val

		if isinstance(rule, _rule_types):
			# set a single-rule
			self.__rule = (_single(rule),)
			return

		# now, we're dealing with multiple rules provided

		def _process_rule_item(item):
			if isinstance(item, _rule_types):
				return _single(item)
			item = err.WrongTypeError(item, (list, tuple), 'rule item').raise_if_needed()
			nu_item = list()
			for it in item:
				it = err.WrongTypeError(it, _rule_types, 'rule item').raise_if_needed()
				if isinstance(it, float):
					it = int(it)
				nu_item.append(it)
			return tuple(nu_item)

		rule = err.WrongTypeError(rule, (list, tuple), 'rule').raise_if_needed()
		self.__rule = tuple([_process_rule_item(x) for x in rule])

	def set_rule(self, rule):
		self.__set_rule(rule)
		return self

	@property
	def rule(self):
		return self.__rule

	@rule.setter
	def rule(self, value):
		self.__set_rule(value)

	@property
	def is_keep(self):
		return self.__is_keep

	@is_keep.setter
	def is_keep(self, value):
		self.__is_keep = bool(value)

	@staticmethod
	def __checked_shape(obj, selection_if_none=True):
		obj = ls.to_objects(
			obj, selection_if_none,
			shape_to_object=False, component_to_shape=True, remove_duplicates=True
		)
		obj = err.NoValueError('obj').raise_if_false(obj)
		if len(obj) > 1:
			raise err.WrongValueError(obj, 'obj', 'a single Transform/Shape')
		obj = obj[0]
		return obj if isinstance(obj, _t_shape_any) else ls.to_shapes(obj, False)[0]

	def __get_matching_sets(self, shape, all_sets=None):
		"""
		Get all matching sets of this rule, applied to a specific poly shape
		"""
		if all_sets is None:
			all_sets = uv_sets.get_object_sets(shape)
		num_sets = len(all_sets)

		def _single_rule(single_rule):
			"""
			Return the matching UV set (if any) for a single rule element.
			I.e., for ('LM_out', 'LM', 10, -5) it will return:
			* 'LM_out', if exist
			* 'LM', if exist
			* 10th UV-set's name, counting from start - if there are at least 10 UV-sets
			* 5th UV-set's name, counting from end - if there are at least 5 UV-sets
			* None, if no match is found
			"""
			for itm in single_rule:

				if isinstance(itm, int):
					#item is int:
					if itm == 0:
						# 0 = current set
						return uv_sets.get_current(shape)
					if itm > 0:
						# positive = set number, starting at 1
						set_id = itm - 1
						if set_id < num_sets:
							return all_sets[set_id]
					# negative = set number, counted from end
					if abs(itm) <= num_sets:
						return all_sets[itm]

				set_nm = err.NotStringError(itm, 'rule item').raise_if_needed()
				if not set_nm:
					return uv_sets.get_current(shape)
				if set_nm in all_sets:
					return set_nm

			return None

		res = list()
		for r in self.__rule:
			match = _single_rule(r)
			if not (match is None):
				res.append(match)
		return utils.remove_duplicates(res)

	def kept_sets_for_object(self, obj, selection_if_none=True):
		shape = UVSetsRule.__checked_shape(obj, selection_if_none)
		all_sets = uv_sets.get_object_sets(shape)
		match = self.__get_matching_sets(shape, all_sets)
		if self.is_keep:
			return match
		return [x for x in all_sets if not (x in match)]

	def removed_sets_for_object(self, obj, selection_if_none=True):
		shape = UVSetsRule.__checked_shape(obj, selection_if_none)
		all_sets = uv_sets.get_object_sets(shape)
		match = self.__get_matching_sets(shape, all_sets)
		if not self.is_keep:
			return match
		return [x for x in all_sets if not (x in match)]

	def __repr__(self):
		return 'UVSetsRule({0}, {1})'.format(repr(self.__rule), repr(self.__is_keep))

	def __str__(self):
		return '<{mode} UVSetsRule: {rule}>'.format(
			mode=('Removed', 'Kept')[self.__is_keep],
			rule=repr(self.__rule)
		)

	def __eq__(self, other):
		"""
		Equality test.
		"""
		if not isinstance(other, self.__class__):
			if isinstance(other, _rule_types):
				return self.__eq__(UVSetsRule(other))
			if isinstance(other, (list, tuple)):
				all_ok = True
				for r in other:
					if isinstance(r, _rule_types):
						continue
					if not isinstance(r, (list, tuple)):
						all_ok = False
						break
					if not all([isinstance(x, _rule_types) for x in r]):
						all_ok = False
						break
				if all_ok:
					return self.__eq__(UVSetsRule(other))
			return NotImplemented
		return self.__dict__ == other.__dict__

	def __ne__(self, other):
		"""
		Non-equality test.
		"""
		res = self.__eq__(other)
		if res == NotImplemented:
			return NotImplemented
		return not res

	def __hash__(self):
		"""
		Override the default hash behavior (that returns the id of the object).
		Used for making sets() of UVSetsRule work properly.
		"""
		return hash(tuple(sorted(self.__dict__.items())))


def _keep_all_rule():
	return UVSetsRule((), is_keep=False)


class UVSets(__BaseProcessor):
	"""
	This is a class performing UV-sets cleanup.
	I.e., it keeps/removes only those UV-sets which pass the list of given UVSetsRule's.
	"""
	def __init__(
		self, items=None, selection_if_none=True, hierarchy=False,
		kept_sets_rule=None
	):
		super(UVSets, self).__init__(
			items=None, selection_if_none=False,
			hierarchy=hierarchy
		)
		self.__set_items(items, selection_if_none)
		self.__kept_sets_rule = _keep_all_rule()
		self.__set_kept_sets_rule(kept_sets_rule)

	def __set_items(self, items=None, selection_if_none=True):
		items = ls.to_geo_nodes(items, selection_if_none, remove_duplicates=True)
		super(UVSets, self).set_items(items, selection_if_none)

	def set_items(self, items=None, selection_if_none=True):
		self.__set_items(items, selection_if_none)
		return self

	def __set_kept_sets_rule(self, rule, is_keep=True):
		if isinstance(rule, UVSetsRule):
			self.__kept_sets_rule = rule
			return
		if rule is None:
			self.__kept_sets_rule = _keep_all_rule()
			return
		self.__kept_sets_rule = UVSetsRule(rule, is_keep)

	@property
	def kept_sets_rule(self):
		res = self.__kept_sets_rule
		assert isinstance(res, UVSetsRule)
		return res

	@kept_sets_rule.setter
	def kept_sets_rule(self, value):
		self.__set_kept_sets_rule(value)

	def get_shapes(self):
		"""
		Converts the list of specified items to their shapes.

		:return: <list of PyNodes> shapes.
		"""
		return ls.to_shapes(self.get_geo_items(), False, exact_type=pm.nt.Mesh)

	def remove_extra_sets(self):
		"""
		Perform the remove of the matching sets for provided objects.

		:return:
			list of 2-value tuples, describing which sets was removed:
				* <PyNode> shape containing sets
				* <tuple of strings> UV-set names
		"""
		shapes = self.get_shapes()
		rule = self.__kept_sets_rule
		res = list()
		for s in shapes:
			removed_sets = rule.removed_sets_for_object(s, False)
			removed = uv_sets.remove(s, removed_sets, False)
			if removed:
				res.extend(removed)
		return res

	def rename_first_set(self, name='map1'):
		shapes = self.get_shapes()
		return uv_sets.rename(shapes, 1, name, False)