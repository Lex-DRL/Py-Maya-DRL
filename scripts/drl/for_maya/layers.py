__author__ = 'Lex Darlog (DRL)'

import warnings as wrn

from maya import cmds, mel
from pymel import core as pm

from . import channel_box as cb


class OverridesFromChannelBox(object):
	def __init__(self, layer=None, channel_box=''):
		super(OverridesFromChannelBox, self).__init__()
		self.__cb_data = cb.ChannelBoxData(channel_box)
		self.layer = layer

	@property
	def channel_box_data(self):
		return self.__cb_data

	@channel_box_data.setter
	def channel_box_data(self, value):
		self.__cb_data = cb.ChannelBoxData(value)

	def attributes(self):
		return self.channel_box_data.all_selected_attributes()

	def __edit_override(self, attribs_listing_f=None, **kwargs):
		if attribs_listing_f is None:
			attr = self.attributes()
		else:
			attr = attribs_listing_f()

		if not self.layer is None:
			kwargs['layer'] = self.layer
		for a in attr:
			pm.editRenderLayerAdjustment(a, **kwargs)
		return attr

	def add(self):
		"""
		Adds overrides for all the attributes selected in Channel Box.
		:return: list of processed attributes
		"""
		return self.__edit_override()

	def remove(self):
		"""
		Removes overrides for all the attributes selected in Channel Box.
		:return: list of processed attributes
		"""
		return self.__edit_override(remove=True)

	def __transform_attribs(self, translate=False, rotate=False, scale=False, shear=False):
		objects = self.channel_box_data.selected_objects()
		attribs = list()
		if translate:
			attribs.append('translate')
		if rotate:
			attribs.append('rotate')
		if scale:
			attribs.append('scale')
		if shear:
			attribs.append('shear')

		ovr_attr = list()
		for o in objects:
			for a in attribs:
				ovr_attr.append(pm.Attribute(o + '.' + a))

		return ovr_attr

	def add_transform(self, translate=False, rotate=False, scale=False, shear=False):
		"""
		Adds overrides for the transform attributes.
		:return: list of processed attributes
		"""
		return self.__edit_override(
			lambda: self.__transform_attribs(translate, rotate, scale, shear)
		)

	def remove_transform(self, translate=False, rotate=False, scale=False, shear=False):
		"""
		Removes overrides for the transform attributes.
		:return: list of processed attributes
		"""
		return self.__edit_override(
			lambda: self.__transform_attribs(translate, rotate, scale, shear),
			remove=True
		)


def with_prefix(prefix, exclude_default=False):
	"""
	Returns the list of display layers with the given prefix.
	No matches if the prefix parameter is empty.
	"""
	if prefix == '':
		return []

	layers_all = cmds.ls(type="displayLayer")
	if exclude_default and ('defaultLayer' in layers_all):
		layers_all.remove('defaultLayer')

	layers = []
	for lr in layers_all:
		if lr.startswith(prefix):
			layers.append(lr)
	return layers



def selected(display=False, render=False):
	"""
	Returns the list of selected layers in the Layer editor.
	Takes into account either display or render layers, depending on the given mode.
	"""
	if not (display or render):
		msg = '\nNot "display" nor "render" mode is set in the call for the selected_layers function.'
		wrn.warn(msg, RuntimeWarning, stacklevel=2)
		return []
	if display:
		mode = 'Display'
	else:
		mode = 'Render'
	return mel.eval('getLayerSelection("%s")' % mode)



def selected_with_warning(display=False, render=False, stacklevel=2):
	layers = selected(display=display, render=render)
	if not layers:
		msg = '\nNo layers selected... HOW THE HELL DID YOU DO IT???'
		wrn.warn(msg, RuntimeWarning, stacklevel=stacklevel)
	return layers



def selected_to_objects():
	"""
	Lists all the objects contained in selected layers
	:return: list of objects/components
	"""
	layers = selected_with_warning(display=True, stacklevel=3)
	if not layers:
		return []
	objects = []
	for lr in layers:
		objects += cmds.editDisplayLayerMembers(lr, q=1, fullNames=1)
	return objects