__author__ = 'DRL'

from maya import cmds
import warnings as wrn

from drl.for_maya import ls
from drl_common.py_2_3 import (
	str_t as _str_t,
	str_h as _str_h,
	xrange as _xrange,
)


class CountedObj(object):
	def __init__(self, obj_path=None, local_space=False, selection_if_empty=True):
		try:
			self.__path = CountedObj.__error_check_init(obj_path, selection_if_empty)
			self.__nm = ls.convert.hierarchy.to_names(self.__path, False)[0]
			self.__loc_space = local_space
			self.refresh()
		except:
			raise

	def refresh(self):
		if self.__loc_space:
			kwargs = {'a': True}
		else:
			kwargs = {'wa': True}
		self.__area = cmds.polyEvaluate(self.__path, **kwargs)

	@property
	def local_space(self):
		return self.__loc_space

	# setter doesn't work in Py2.5 (Maya 2009), so...

	def set_space(self, local=False):
		if not isinstance(local, bool):
			local = bool(local)
		self.__loc_space = local
		self.refresh()

	@property
	def name(self):
		return self.__nm

	@property
	def path(self):
		return self.__path

	@property
	def area(self):
		return self.__area

	def __call__(self, *args, **kwargs):
		return self.path, self.name, self.area

	def __repr__(self):
		return '< CountedObj: "%s", %s >' % (self.name, self.area)

	def __str__(self):
		return self.__repr__()

	@staticmethod
	def __errorstring(err='', namespace='CountedObj', methodname=''):
		res = ''

		if not(
			isinstance(namespace, str) and
			isinstance(methodname, str) and
			isinstance(err, str)
		):
			return ''

		if methodname:
			if namespace:
				res = '.'.join([namespace, methodname])
			else:
				res = methodname
			res += '()'
		else:
			res = namespace

		if err:
			if res:
				res += ': ' + err
			else:
				res = err

		return res

	@staticmethod
	def __error_check_init(objPath, selection_if_empty=True):
		if isinstance(objPath, (list, tuple)):
			if objPath:
				msg = '\nList or tuple provided instead of string. Extracting 1st element: "%s"' % objPath
				wrn.warn(CountedObj.__errorstring(msg), RuntimeWarning, stacklevel=3)
				return CountedObj.__error_check_init(objPath[0], selection_if_empty)
			elif selection_if_empty:
				objPath = None
			else:
				raise Exception(CountedObj.__errorstring('Empty list or tuple is given'))
		elif isinstance(objPath, set):
			if selection_if_empty:
				objPath = None
			else:
				raise Exception(CountedObj.__errorstring('Set provided instead of string'))
		elif not isinstance(objPath, _str_t):
			if selection_if_empty:
				objPath = None
			else:
				raise Exception(CountedObj.__errorstring('Wrong argument type, string expected'))

		# make sure this shape actually exist:
		if not cmds.ls(objPath):
			if selection_if_empty:
				objPath = None
			else:
				raise Exception(CountedObj.__errorstring("Provided object doesn't exist in the scene: %s" % objPath))
		# ... and that it is a polygonal shape:
		elif not cmds.ls(ls.convert.hierarchy.to_shapes(objPath, False, True), type='mesh'):
			if selection_if_empty:
				objPath = None
			else:
				raise Exception(CountedObj.__errorstring("Provided object is not a polygonal transform: %s" % objPath))

		objPath = ls.convert.hierarchy.to_full_paths(objPath, False)

		if objPath:
			objPath = objPath[0]
		elif selection_if_empty:
			sel = ls.default_input.selection()
			return CountedObj.__error_check_init(sel, False)

		if not objPath:
			raise Exception(CountedObj.__errorstring('No objects selected'))

		return objPath

	@staticmethod
	def obj_path(obj):
		if isinstance(obj, _str_t):
			objPath = ls.convert.hierarchy.to_full_paths(obj, False)[0]
			if objPath:
				return objPath
			else:
				raise Exception('No such object in the scene: %s' % obj)
		elif isinstance(obj, CountedObj):
			return obj.path
		else:
			raise Exception('Given <obj> argument is not a string or CountedObj.')



class ObjectGroup(object):
	def __init__(self, objs=None, local_space=False, selection_if_empty=True):
		self.__count = 0.0
		self.__objs = list()
		self.__loc_space = local_space
		if objs is None or not objs:
			if selection_if_empty:
				objs = ls.default_input.selection()
			else:
				objs = list()
		elif isinstance(objs, _str_t):
			objs = [objs]
		elif isinstance(objs, tuple):
			objs = list(objs)
		elif not isinstance(objs, list):
			objs = list()
		self.append(objs)

	def obj(self, index=0):
		return self.__objs[index]

	def obj_paths(self):
		return [x.path for x in self.__objs]

	def obj_index(self, obj):
		try:
			objPath = CountedObj.obj_path(obj)
		except:
			raise
		return self.obj_paths().index(objPath)

	def sort(self, decreasing=True):
		self.__objs.sort(key=lambda o: o.area, reverse=decreasing)

	def remove(self, obj):
		if self.is_obj_in_group(obj):
			idx = self.obj_index(obj)
			area = self.__objs[idx].area
			del(self.__objs[idx])
			self.__count -= area
		if not self.__objs:
			self.__count = 0.0

	def is_obj_in_group(self, obj):
		try:
			objPath = CountedObj.obj_path(obj)
		except:
			raise
		return objPath in self.obj_paths()

	__t_str_or_instance = tuple(list(_str_t) + [CountedObj])

	def append(self, objs=None, selection_if_empty=True):
		if isinstance(objs, self.__t_str_or_instance) and objs:
			objs = [objs]
		elif isinstance(objs, tuple):
			objs = list(objs)
		elif not isinstance(objs, list):
			objs = list()

		if not objs and selection_if_empty:
			objs = ls.default_input.selection()

		for o in objs:
			try:
				if isinstance(o, CountedObj):
					nuObj = o
				else:
					nuObj = CountedObj(o, self.__loc_space, False)
				if not self.is_obj_in_group(nuObj.path):
					self.__objs.append(nuObj)
					self.__count += nuObj.area
			except:
				pass

	@property
	def total_area(self):
		return self.__count

	def __len__(self):
		return len(self.__objs)

	def __repr__(self):
		if self.__loc_space:
			space = 'local'
		else:
			space = 'world'
		return '< ObjectGroup: %s space, %d objects, %f total area >' % (space, len(self), self.__count)

	def __str__(self):
		return self.__repr__()

	def __call__(self, *args, **kwargs):
		return self.__objs[:]



class GroupedObjects(object):
	def __init__(self, groupNum = 2, objs=None, local_space=False, selection_if_empty=True):
		self.__ungrouped = ObjectGroup(objs, local_space, selection_if_empty)
		self.__loc_space = local_space
		self.__groups = list()
		for i in _xrange(groupNum):
			self.add_group(None, False)

	def add_group(self, objs=None, selection_if_empty=True):
		self.__groups.append(ObjectGroup(objs, self.__loc_space, selection_if_empty))

	def get_group(self, group_index=0):
		return self.__groups[group_index]

	def grouped_objects(self):
		res = list()
		for g in self.__groups:
			res += g.obj_paths()
		return res

	def add_objects(self, group_index=None, objs=None, selection_if_empty=True):
		'''
		Adds objects to the end of a group.
		If optional group_index argument is provided and is valid integer group index,
		objects are added to a specific group.
		Otherwise, they're added to a "ungrouped" queue.
		:return: None
		'''
		if isinstance(group_index, int):
			append_to = self.get_group(group_index)
		else:
			append_to = self.ungrouped()
		append_to.append(objs, selection_if_empty)

	def sort_groups(self, decreasing=False):
		'''
		Sorts existing groups from the one with the smallest total area
		to the one with the biggest. Or vice versa, if <decreasing> argument is True.
		:return: None
		'''
		self.__groups.sort(key=lambda gr: gr.total_area, reverse=decreasing)

	def __sorted_groups(self, decreasing=False, to_groups=None):
		if isinstance(to_groups, list) and to_groups:
			groups = list()
			for i, g in enumerate(self.__groups):
				if i in to_groups:
					groups.append(g)
		else:
			groups = self.__groups
		return sorted(groups, key=lambda gr: gr.total_area, reverse=decreasing)

	def __smallest_group(self, to_groups=None):
		return self.__sorted_groups(False, to_groups)[0]

	def __biggest_group(self, to_groups=None):
		return self.__sorted_groups(True, to_groups)[0]

	def group_ungrouped(self, to_groups=None):
		queue = self.__ungrouped
		while queue:
			queue.sort()
			paths = queue.obj_paths()
			for p in paths:
				smallest_gr = self.__smallest_group(to_groups)
				queue.remove(p)
				smallest_gr.append(p, False)

	def ungrouped(self):
		return self.__ungrouped

	def __len__(self):
		return len(self.__groups)

	def __repr__(self):
		if self.__loc_space:
			space = 'local'
		else:
			space = 'world'
		return '< GroupedObjects: %s space, %d objects in %d groups, %d ungrouped objects >' % (space, len(self.grouped_objects()), len(self), len(self.ungrouped()))

	def __str__(self):
		return self.__repr__()

	def __call__(self, *args, **kwargs):
		return self.__groups[:]