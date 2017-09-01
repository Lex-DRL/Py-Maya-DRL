__author__ = 'DRL'

from pymel import core as pm
from drl_common.strings import str_types


class ChannelBoxData(object):
	def __init__(self, channel_box=''):
		"""
		High-level class allowing to get some common data from a channel box.
		If optional <channel_box> argument is omitted, the main (global) channel box is used.

		:param channel_box: one of:
			* string (UI path name to the channel box)
			* instance of pm.uitypes.ChannelBox
			* instance of another ChannelBoxData
		"""
		super(ChannelBoxData, self).__init__()
		self.__set_cb(channel_box)


	def __set_cb(self, val):
		if isinstance(val, ChannelBoxData):
			self.__cb = val.channel_box
			return

		if isinstance(val, pm.uitypes.ChannelBox):
			if not val:
				raise Exception("The provided Channel Box doesn't exist: " + repr(val))
			self.__cb = val
			return

		if not val:
			val = ChannelBoxData.main_box_ui_name()
		elif not isinstance(val, str_types):
			raise Exception(
				'The <channel_box> property needs to be either string or uitypes.ChannelBox. Got: ' + repr(val)
			)
		self.__cb = pm.uitypes.ChannelBox(val)

	@property
	def channel_box(self):
		return self.__cb

	@channel_box.setter
	def channel_box(self, value):
		self.__set_cb(value)


	@staticmethod
	def main_box_ui_name():
		try:
			cb_name = pm.melGlobals['gChannelBoxName']
		except:
			cb_name = 'mainChannelBox'
			pm.melGlobals.initVar('string', 'gChannelBoxName')
			pm.melGlobals['gChannelBoxName'] = cb_name
		return cb_name


	def __selected_f(self, func):
		res = func(self.channel_box)
		if not res:
			res = []
		assert isinstance(res, list)
		return res

	def selected_objects(self):
		return self.__selected_f(lambda x: x.getMainObjectList())

	def selected_shapes(self):
		return self.__selected_f(lambda x: x.getShapeObjectList())

	def selected_input_objects(self):
		return self.__selected_f(lambda x: x.getHistoryObjectList())

	def selected_output_objects(self):
		return self.__selected_f(lambda x: x.getOutputObjectList())

	def selected_attributes_main(self):
		return self.__selected_f(lambda x: x.getSelectedMainAttributes())

	def selected_attributes_inputs(self):
		return self.__selected_f(lambda x: x.getSelectedHistoryAttributes())

	def selected_attributes_outputs(self):
		return self.__selected_f(lambda x: x.getSelectedOutputAttributes())

	def selected_attributes_shape(self):
		return self.__selected_f(lambda x: x.getSelectedShapeAttributes())

	def all_selected_attributes(self):
		"""
		Lists <Attribute> objects for all the attributes and all the objects
		selected in the ChannelBox, including attributes in
		"Shapes", "Inputs" and "Output" sections.

		:return: list of pm.Attribute instances.
		"""
		return [pm.Attribute(a) for a in self.all_selected_attributes_paths()]

	def all_selected_attributes_paths(self):
		"""
		Lists <attribute names> for all the attributes and all the objects
		selected in the ChannelBox, including attributes in
		"Shapes", "Inputs" and "Output" sections.

		:return: list of strings with full attribute paths
		"""
		res = list()
		objects_f_tuple = (
			self.selected_objects,
			self.selected_shapes,
			self.selected_input_objects,
			self.selected_output_objects
		)
		attribs_f_tuple = (
			self.selected_attributes_main,
			self.selected_attributes_shape,
			self.selected_attributes_inputs,
			self.selected_attributes_outputs
		)

		def add_res(obj_f, attr_f):
			attribs = attr_f()
			objs = obj_f()
			attr_list = list()
			for o in objs:
				for a in attribs:
					attr_list.append(o + '.' + a)
			return attr_list

		attribs_twolevel = map(add_res, objects_f_tuple, attribs_f_tuple)
		for l in attribs_twolevel:
			res += l

		return res