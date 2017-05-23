__author__ = 'DRL'

from pymel import core as pm

default_regex = r'^.+_%s[_\d]*$'


def meshes(match_regex=None):
	"""
	Select source trees (transforms) first, their shapes will replace
	all the other trees in the scene, if they're named correspondingly.

	:param match_regex: Optional regular expression that determines the rule to match new object's name with the old one. If none provided, default is used.
	:return: list of updated transforms
	"""
	import re
	from drl.for_maya import geo
	reload(geo)
	from drl.for_maya.ls import pymel as ls
	reload(ls)
	src_objects = pm.ls(sl=1, tr=1)
	# src = src_objects[0]

	if match_regex is None or not isinstance(match_regex, (str, unicode)):
		match_regex = default_regex

	res = list()

	for src in src_objects:
		shape = ls.to_shapes(src, False, geo_surface=True)[0]
		children = pm.listRelatives(src, children=1, type='transform')
		src_nm = ls.short_item_name(src)
		regex_compiled = re.compile(match_regex % src_nm)
		targets = [
			t for t in pm.ls('*%s*' % src_nm, tr=1)
			if (
				t != src and
				regex_compiled.match(ls.short_item_name(t))
			)
		]
		targets = geo.instance_to_object(targets, False)
		for t in targets:
			pm.delete(pm.listRelatives(t, children=1))  # remove
			res.append(pm.parent(shape, t, shape=1, relative=1, addObject=1))
			for c in children:
				dup = pm.instance(c, leaf=1)[0]
				dup = pm.parent(dup, t, relative=1)[0]
				dup = pm.rename(dup, ls.short_item_name(c))
				res.append(dup)

	pm.select(res, r=1)
	return res


def meshes_and_transforms(match_regex=None):
	"""
	Designed to replace the current trees (made of old shapes with old pivot) with the new ones.
	I.e., this function updates not only a mesh, but also it's transform.

	Select source trees (transforms) first, their shapes will replace
	all the other trees in the scene, if they're named correspondingly.

	Each tree has to be parented to a transform representing the old tree mesh. I.e.:
	* to_parent - old tree geo, with old pivot/transform
	* child - new tree geo (shape is changed/offset relatively to pivot/transform)

	to_parent and child need to look the same (but, obviously, child's transform is offset)

	:param match_regex: Optional regular expression that determines the rule to match new object's name with the old one. If none provided, default is used.
	:return: list of updated transforms
	"""
	import re
	from drl.for_maya import geo
	reload(geo)
	from drl.for_maya.ls import pymel as ls
	reload(ls)
	src_objects = pm.ls(sl=1, tr=1)
	# src = src_objects[0]

	if match_regex is None or not isinstance(match_regex, (str, unicode)):
		match_regex = default_regex

	res = list()

	for src in src_objects:
		local_xform = pm.xform(src, q=1, relative=1, objectSpace=1, matrix=1)

		shape = ls.to_shapes(src, False, geo_surface=True)[0]
		children = pm.listRelatives(src, children=1, type='transform')
		src_nm = ls.short_item_name(src)
		regex_compiled = re.compile(match_regex % src_nm)
		targets = [
			t for t in pm.ls('*%s*' % src_nm, tr=1)
			if (
				t != src and
				regex_compiled.match(ls.short_item_name(t))
			)
		]
		targets = geo.instance_to_object(targets, False)
		for t in targets:
			tmp_dup = pm.duplicate(src)[0]
			tmp_dup = pm.parent(tmp_dup, t, relative=1)[0]
			pm.xform(tmp_dup, absolute=1, objectSpace=1, matrix=local_xform)
			ws_xform = pm.xform(tmp_dup, q=1, absolute=1, worldSpace=1, matrix=1)

			pm.delete(pm.listRelatives(t, children=1))  # remove
			pm.xform(t, absolute=1, worldSpace=1, matrix=ws_xform)
			res.append(pm.parent(shape, t, shape=1, relative=1, addObject=1))
			for c in children:
				dup = pm.instance(c, leaf=1)[0]
				dup = pm.parent(dup, t, relative=1)[0]
				dup = pm.rename(dup, ls.short_item_name(c))
				res.append(dup)

	pm.select(res, r=1)
	return res