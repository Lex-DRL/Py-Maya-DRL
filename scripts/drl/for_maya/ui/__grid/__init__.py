__author__ = 'DRL'


from . import var_names as _v


# We need to create a metaclass to use static properties:

class _GridMeta(type):
	# We'll use default __new__ from type, since this metaclass
	# doesn't create any members other than properties
	# def __new__(mcs, *args, **kwargs):
	# 	return super(_GridMeta, mcs).__new__(mcs, *args, **kwargs)

	@property
	def enabled(self):
		"""
		Turns the ground plane display off in all windows, including orthographic windows.

		Default is true.

		:rtype: bool
		"""
		return _v.enabled.property_value

	@enabled.setter
	def enabled(self, value):
		"""
		Turns the ground plane display off in all windows, including orthographic windows.

		Default is true.

		:type value: bool
		"""
		_v.enabled.property_value = value

	@property
	def size(self):
		"""
		Sets the size of the grid in linear units.

		The default is 12 units.

		:rtype: float
		"""
		return _v.size.property_value

	@size.setter
	def size(self, value):
		"""
		Sets the size of the grid in linear units.

		The default is 12 units.

		:type value: int | float
		"""
		_v.size.property_value = value

	@property
	def spacing(self):
		"""
		Sets the spacing between major grid lines in linear units.

		The default is 5 units.

		:rtype: float
		"""
		return _v.spacing.property_value

	@spacing.setter
	def spacing(self, value):
		"""
		Sets the spacing between major grid lines in linear units.

		The default is 5 units.

		:type value: int | float
		"""
		_v.spacing.property_value = value

	@property
	def divisions(self):
		"""
		Sets the number of subdivisions between major grid lines.

		The default is 5. If the spacing is 5 units, setting divisions to 5 will cause division lines to appear 1 unit apart.

		:rtype: int
		"""
		return _v.divisions.property_value

	@divisions.setter
	def divisions(self, value):
		"""
		Sets the number of subdivisions between major grid lines.

		The default is 5. If the spacing is 5 units, setting divisions to 5 will cause division lines to appear 1 unit apart.

		:type value: int
		"""
		_v.divisions.property_value = value

	@property
	def axes(self):
		"""
		Whether the grid axes are visible.

		:rtype: bool
		"""
		return _v.axes.property_value

	@axes.setter
	def axes(self, value):
		"""
		Whether the grid axes are visible.

		:type value: bool
		"""
		_v.axes.property_value = value

	@property
	def axes_bold(self):
		"""
		Specify true to accent the grid axes by drawing them with a thicker line.

		:rtype: bool
		"""
		return _v.axes_bold.property_value

	@axes_bold.setter
	def axes_bold(self, value):
		"""
		Specify true to accent the grid axes by drawing them with a thicker line.

		:type value: bool
		"""
		_v.axes_bold.property_value = value

	@property
	def lines(self):
		"""
		Specify true to display the grid lines.

		:rtype: bool
		"""
		return _v.lines.property_value

	@lines.setter
	def lines(self, value):
		"""
		Specify true to display the grid lines.

		:type value: bool
		"""
		_v.lines.property_value = value

	@property
	def lines_subdivision(self):
		"""
		Specify true to display the subdivision lines between grid lines.

		:rtype: bool
		"""
		return _v.lines_subdivision.property_value

	@lines_subdivision.setter
	def lines_subdivision(self, value):
		"""
		Specify true to display the subdivision lines between grid lines.

		:type value: bool
		"""
		_v.lines_subdivision.property_value = value

	@property
	def labels_persp(self):
		"""
		Specify true to display the grid line numeric labels in the perspective view.

		:rtype: bool
		"""
		return _v.labels_persp.property_value

	@labels_persp.setter
	def labels_persp(self, value):
		"""
		Specify true to display the grid line numeric labels in the perspective view.

		:type value: bool
		"""
		_v.labels_persp.property_value = value

	@property
	def labels_ortho(self):
		"""
		Specify true to display the grid line numeric labels in the orthographic views.

		:rtype: bool
		"""
		return _v.labels_ortho.property_value

	@labels_ortho.setter
	def labels_ortho(self, value):
		"""
		Specify true to display the grid line numeric labels in the orthographic views.

		:type value: bool
		"""
		_v.labels_ortho.property_value = value

	@property
	def labels_persp_pos(self):
		"""
		The position of the grid's numeric labels in perspective views.

		Valid values are:
			* "axis"
			* "edge"

		:rtype: unicode
		"""
		return _v.labels_persp_pos.property_value

	@labels_persp_pos.setter
	def labels_persp_pos(self, value):
		"""
		The position of the grid's numeric labels in perspective views.

		Valid values are:
			* "axis"
			* "edge"

		:type value: str | unicode
		"""
		_v.labels_persp_pos.property_value = value

	@property
	def labels_ortho_pos(self):
		"""
		The position of the grid's numeric labels in orthographic views.

		Valid values are:
			* "axis"
			* "edge"

		:rtype: unicode
		"""
		return _v.labels_ortho_pos.property_value

	@labels_ortho_pos.setter
	def labels_ortho_pos(self, value):
		"""
		The position of the grid's numeric labels in orthographic views.

		Valid values are:
			* "axis"
			* "edge"

		:type value: str | unicode
		"""
		_v.labels_ortho_pos.property_value = value


# Python 3 style:
# class Grid(metaclass=_Grid):
# 	def __init__(self):
# 		pass


class Grid(object):
	"""
	The service class providing access to the viewport's grid settings.
	The main difference from default cmds.grid() is that this class also
	tracks the corresponding optionVars and sets them accordingly.

	The class is static, so you don't need to create an instance of it.

	You can call it's constructor, however. It acts as a shorthand for
	setting multiple grid properties at once.
	"""
	__metaclass__ = _GridMeta

	def __init__(
		self, enabled=None, size=None, spacing=None, divisions=None,
		axes=None, axes_bold=None, lines=None, lines_subdivision=None,
		labels_persp=None, labels_ortho=None, labels_persp_pos=None, labels_ortho_pos=None
	):
		"""
		The service class providing access to the viewport's grid settings.
		The main difference from default cmds.grid() is that this class also
		tracks the corresponding optionVars and sets them accordingly.

		The class is static, so you don't need to create an instance of it.

		This constructor is just a shorthand for setting
		multiple grid properties at once.

		:type enabled: bool
		:param enabled:
			Turns the ground plane display off in all windows,
			including orthographic windows.
		:type size: int | float
		:param size: Sets the size of the grid in linear units.
		:type spacing: int | float
		:param spacing: Sets the spacing between major grid lines in linear units.
		:type divisions: int
		:param divisions: Sets the number of subdivisions between major grid lines.
		:type axes: bool
		:param axes: Whether the grid axes are visible.
		:type axes_bold: bool
		:param axes_bold:
			Specify true to accent the grid axes
			by drawing them with a thicker line.
		:type lines: bool
		:param lines: Specify true to display the grid lines.
		:type lines_subdivision: bool
		:param lines_subdivision:
			Specify true to display the subdivision lines between grid lines.
		:type labels_persp: bool
		:param labels_persp:
			Specify true to display the grid line numeric labels
			in the perspective view.
		:type labels_ortho: bool
		:param labels_ortho:
			Specify true to display the grid line numeric labels
			in the orthographic views.
		:type labels_persp_pos: str | unicode
		:param labels_persp_pos:
			The position of the grid's numeric labels in perspective views.

			Valid values are:
				* "axis"
				* "edge"
		:type labels_ortho_pos: str | unicode
		:param labels_ortho_pos:
			The position of the grid's numeric labels in orthographic views.

			Valid values are:
				* "axis"
				* "edge"
		"""
		if enabled is not None:
			Grid.enabled = enabled
		if size is not None:
			Grid.size = size
		if spacing is not None:
			Grid.spacing = spacing
		if divisions is not None:
			Grid.divisions = divisions
		if axes is not None:
			Grid.axes = axes
		if axes_bold is not None:
			Grid.axes_bold = axes_bold
		if lines is not None:
			Grid.lines = lines
		if lines_subdivision is not None:
			Grid.lines_subdivision = lines_subdivision
		if labels_persp is not None:
			Grid.labels_persp = labels_persp
		if labels_ortho is not None:
			Grid.labels_ortho = labels_ortho
		if labels_persp_pos is not None:
			Grid.labels_persp_pos = labels_persp_pos
		if labels_ortho_pos is not None:
			Grid.labels_ortho_pos = labels_ortho_pos
		# super(Grid, self).__init__()

	@staticmethod
	def reset():
		_v.reset()

	@staticmethod
	def update_option_vars():
		_v.update_option_vars()

	@staticmethod
	def set():
		pass
