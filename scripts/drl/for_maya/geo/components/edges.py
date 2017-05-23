__author__ = 'DRL'

import maya.cmds as cmds

from ...input_warn import items_input as wrn_items

def to_edges(items=None, flatten=False, stacklevel_offset=0):
	'''
	Converts the provided list of items (doesn't matter if there are objects or components) to the edges.

	:param items: List of items. Error-check is performed.
	:param flatten: whether or not the resulting list needs to be flattened.
	:param stacklevel_offset: it's used to define the level of warnings.
	:return: list of edges
	'''
	items = wrn_items(items, stacklevel_offset=1+stacklevel_offset)
	if isinstance(items, type(None)):
		return []

	edges = cmds.polyListComponentConversion(items, te=1)  # convert list of items to edges
	if flatten:
		edges = cmds.ls(edges, fl=1)  # and make sure they're listed one-by-one, if needed
	return edges



def filter_to_hardEdges(edges=None, flatten=False):
	'''
	Checks which of the given edges are hard.

	:param edges: the list of edges. WARNING: it may not contain anything else.
	:param flatten: whether resulting list needs to be flattened or compact. Compact by default (uses less memory).
	:return: the list of hard edges.
	'''
	edges = cmds.ls(edges, fl=1)  # make sure edges are listed one-by-one
	hardEdges = []

	for e in edges:
		edgeInfo = cmds.polyInfo(e, ev=1)[0].strip().lower()
		if edgeInfo[:4] == 'edge' and edgeInfo[-4:] == 'hard':
			hardEdges.append(e)

	if not flatten:
		hardEdges = cmds.polyListComponentConversion(hardEdges, te=1)

	return hardEdges



def to_hardEdges(items=None, flatten=False, stacklevel_offset=0):
	'''
	High-level wrapper function, allowing to convert given objects/components to their hard edges.

	:param items: List of items. Doesn't matter whether they're objects or components. Error-check performed.
	:param flatten: whether resulting list needs to be flattened or compact. Compact by default (uses less memory).
	:param stacklevel_offset: it's used to define the level of warnings.
	:return: the list of hard edges.
	'''
	edges = to_edges(items, stacklevel_offset=1+stacklevel_offset)

	return filter_to_hardEdges(edges, flatten=flatten)



def filter_to_borderEdges(edges=None, to_geoBorder=False, to_uvBorder=False, flatten=False):
	'''
	Checks which of the given edges are either geo- or UV-border edges.

	:param edges: the list of edges. WARNING: it may not contain anything else.
	:param to_geoBorder: Whether or not to check for geo-border edges
	:param to_uvBorder: Whether or not to check for UV-border edges
	:param flatten: whether resulting list needs to be flattened or compact. Compact by default (uses less memory).
	:return: the 3-tuple, containing respectively: combined, geo and UV border edges lists. Lists are flattened.
	'''
	edges = cmds.ls(edges, fl=1)  # make sure edges are listed one-by-one

	combinedBorders = []
	geoBorder = []
	uvSeams = []
	geo = False
	uv = False

	if not (to_geoBorder or to_uvBorder):
		return [], [], []

	for e in edges:
		if to_geoBorder:
			# convert the edge to it's respective polygons, listed one-by-one
			convPolys = cmds.polyListComponentConversion(e, tf=1)
			convPolys = cmds.ls(convPolys, fl=1)
			# and if there are less then 2 polys, it's a texture-border edge:
			if len(convPolys) < 2:
				geo = True
				geoBorder.append(e)
			else:
				geo = False
		if to_uvBorder:
			# convert the edge to it's respective UVs, listed one-by-one:
			convUVs = cmds.polyListComponentConversion(e, tuv=1)
			convUVs = cmds.ls(convUVs, fl=1)
			# and if there are more then 2 UVs, it's a texture-border edge:
			if len(convUVs) > 2:
				uv = True
				uvSeams.append(e)
			else:
				uv = False
		if geo or uv:
			combinedBorders.append(e)

	if not flatten:
		combinedBorders = cmds.polyListComponentConversion(combinedBorders, te=1)
		geoBorder = cmds.polyListComponentConversion(geoBorder, te=1)
		uvSeams = cmds.polyListComponentConversion(uvSeams, te=1)

	return combinedBorders, geoBorder, uvSeams



def to_borderEdges(items=None, to_geoBorder=False, to_uvBorder=False, flatten=False, stacklevel_offset=0):
	'''
	High-level wrapper function, allowing to convert given objects/components to their border edges.

	:param items: List of items. Doesn't matter whether they're objects or components. Error-check performed.
	:param to_geoBorder: Whether or not to check for geo-border edges
	:param to_uvBorder: Whether or not to check for UV-border edges
	:param flatten: whether resulting list needs to be flattened or compact. Compact by default (uses less memory).
	:param stacklevel_offset: it's used to define the level of warnings.
	:return: the 3-tuple, containing respectively: combined, geo and UV border edges lists. Lists are flattened.
	'''
	edges = to_edges(items, stacklevel_offset=1+stacklevel_offset)

	return filter_to_borderEdges(edges, to_geoBorder=to_geoBorder, to_uvBorder=to_uvBorder, flatten=flatten)


def to_edgeLoop(items=None, flatten=False, stacklevel_offset=0):
	edges = to_edges(items, stacklevel_offset=1+stacklevel_offset)
	edges = cmds.polySelectSp(edges, q=1, loop=1)
	if flatten:
		edges = cmds.ls(edges, fl=1)  # and make sure they're listed one-by-one, if needed
	return edges


def to_edgeRing(items=None, flatten=False, stacklevel_offset=0):
	edges = to_edges(items, stacklevel_offset=1+stacklevel_offset)
	edges = cmds.polySelectSp(edges, q=1, ring=1)
	if flatten:
		edges = cmds.ls(edges, fl=1)  # and make sure they're listed one-by-one, if needed
	return edges

def to_edgeRing_groups(items=None, flatten=False, stacklevel_offset=0):
	flatEdges = to_edges(items, flatten=True, stacklevel_offset=1+stacklevel_offset)
	res = []
	while flatEdges:
		edgeRing = to_edgeRing(flatEdges.pop(0), stacklevel_offset=1+stacklevel_offset)
		edgeRing_flat = cmds.ls(edgeRing, fl=1)
		if flatten:
			res.append(edgeRing_flat[:])
		else:
			res.append(edgeRing[:])
		del edgeRing
		for e in edgeRing_flat:
			while e in flatEdges:
				flatEdges.remove(e)
	return res

def to_edgeLoop_groups(items=None, flatten=False, stacklevel_offset=0):
	flatEdges = to_edges(items, flatten=True, stacklevel_offset=1+stacklevel_offset)
	res = []
	while flatEdges:
		pass
