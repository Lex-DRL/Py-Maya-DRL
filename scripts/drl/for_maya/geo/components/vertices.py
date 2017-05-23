__author__ = 'DRL'


from pymel import core as pm

from drl.for_maya.ls import pymel as ls
from drl.for_maya.ls.convert import components as comp
from drl.for_maya.ui import ProgressWindow



def snap_point_to_point(
	items=None, selection_if_none=True,
	max_distance=None, min_distance=0.01,
	object_space=False
):
	"""
	Performs point-to-point snap for polygonal meshes.

	Select the components you want to snap first,
	and lastly, select the mesh you want to snap them to.

	:param items: items (objects/components) to snap. The same order expected.
	:param selection_if_none: whether to use selection when no items given.
	:param max_distance: When provided, points will snap only if distance below this range.
	:param min_distance: The minimum distance (allows to leave alone vertices which are already almost there)
	:return: flattened list of vertices that were snapped
	"""
	items = ls.default_input.handle_input(items, selection_if_none, flatten=False)

	if len(items) < 2:
		raise IndexError('Not enough objects provided')
	
	transfer_space = 'object' if object_space else 'world'

	if (
		not isinstance(min_distance, (float, int)) or
		min_distance < 0.0
	):
		min_distance = 0.0

	src = items.pop()
	src = ls.to_shapes(src, False, exact_type=pm.nt.Mesh)[0]
	assert isinstance(src, pm.nt.Mesh)
	src_pos = src.getPoints(space=transfer_space)

	def find_closest(pt):
		closest = src_pos[0]
		closest_len = pt.distanceTo(closest)
		for cur in src_pos[1:]:
			cur_len = pt.distanceTo(cur)
			if cur_len < closest_len:
				closest_len = cur_len
				closest = cur
		return closest, closest_len

	def do_snap(distance):
		return (
			min_distance < distance and (max_distance is None or distance < max_distance)
		)

	res = []

	def snap_item(mesh, base_msg):
		vtxs = comp.convert_poly(mesh, False, tv=True, flatten=True)
		ProgressWindow.message = base_msg + '\t\tverts: %s' % len(vtxs)
		for vrt in vtxs:
			p = vrt.getPosition(space=transfer_space)
			snap_to_p, dist = find_closest(p)
			if do_snap(dist):
				vrt.setPosition(snap_to_p, space=transfer_space)
				res.append(vrt)

	# for i in items:
	# 	snap_item(i)

	num = len(items)
	i = 0
	ProgressWindow('0/%s' % num, 'Transfer (%s space)' % transfer_space, max=num)

	while ProgressWindow.is_active():
		itm = items[i]
		msg = '{0}/{1}: {2}'.format(i + 1, num, itm.name())
		print msg
		# msg += '\nSnap to: {0}\nSpace: {1}'.format(src.name(), transfer_space)
		ProgressWindow.message = msg
		snap_item(itm, msg)
		i += 1
		ProgressWindow.increment()

	ProgressWindow.end()

	return res