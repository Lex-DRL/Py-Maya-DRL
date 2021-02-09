__author__ = 'Lex Darlog (DRL)'

from maya import cmds
from ....input_warn import items_input as wrn_items


def to_vertices(items=None, flatten=False, stacklevel_offset=0):
	"""
	Converts the provided list of items (doesn't matter if there are objects or components) to the edges.

	:param items: List of items (objects/components). Error-check is performed.
	:param flatten: whether or not the resulting list needs to be flattened.
	:param stacklevel_offset: used to define the level of warnings.
	:return: list of edges
	"""
	items = wrn_items(items, stacklevel_offset=1+stacklevel_offset)
	if isinstance(items, type(None)):
		return []

	verts = cmds.polyListComponentConversion(items, tv=1)  # convert list of items to vertices
	if flatten:
		verts = cmds.ls(verts, fl=1)  # and make sure they're listed one-by-one, if needed
	return verts



def calc_unityCount(items=None, stacklevel_offset=0):
	"""
	Calculates number of vertices the same way Unity sees it.

	:param items: List of items (objects/components). Error-check is performed.
	:param stacklevel_offset: used to define the level of warnings.
	:return: number of vertices for the current selection
	"""
	from .. import edges as edg

	items = wrn_items(items, stacklevel_offset=1+stacklevel_offset)
	items = cmds.polyListComponentConversion(items, tf=1) # list of selected faces
	if isinstance(items, type(None)) or not items:
		return 0

	total = cmds.polyEvaluate(items, vertex=1)

	# determine all the geo- and UV-border edges for the current items
	geoBorder, uvBorder = edg.to_borderEdges(
		items,
		to_geoBorder=1,
		to_uvBorder=1,
		flatten=1,
		stacklevel_offset=1+stacklevel_offset
	)[1:3]
	hardEdges = edg.to_hardEdges(items, flatten=1, stacklevel_offset=1+stacklevel_offset)
	edgeSplits = set(hardEdges) - set(geoBorder)
	edgeSplits = edgeSplits | set(uvBorder)
	del hardEdges, uvBorder

	if not edgeSplits:
		return total

	# convert geo border from edges to vertices
	geoBorder = to_vertices(geoBorder, flatten=True)

	verts = to_vertices(edgeSplits, flatten=True)

	for v in verts:
		vertEdges = edg.to_edges(v, flatten=1, stacklevel_offset=1+stacklevel_offset)
		vertSplitEdges = 0
		for e in vertEdges:
			if e in edgeSplits:
				vertSplitEdges += 1

		if v in geoBorder:
			# we're on the border
			total += vertSplitEdges
		else:
			# we're inside the shell
			total += max(0, vertSplitEdges-1)

	return total