from collections import namedtuple
from pymel import core as _pm

from drl_py23 import (
	str_t as _str_t,
	str_h as _str_h,
)


# service namedTuple with all the the names of a grid property
__VarNamesTuple = namedtuple(
	'__VarNamesTuple',
	['kwarg', 'type', 'optionVar', 'globalType', 'globalName']
)


class _VarNames(__VarNamesTuple):
	@property
	def property_value(self):
		"""
		Current grid property.
		Sets the corresponding optionVar to the same value, if it's provided
		and the values differ.

		:return: the current value of the grid property.
		"""
		kwargs = {
			'q': True,
			self.kwarg: True
		}
		res = _pm.grid(**kwargs)

		if not self.optionVar:  # check that we provided an optionVar name
			return res

		reset = False
		option = _pm.optionVar.get(self.optionVar, None)
		if option is None:
			option = self.__get_default()
			reset = True
		if option != res:
			reset = True
		if reset:
			_pm.optionVar[self.optionVar] = self.type(res)
		return res

	@property_value.setter
	def property_value(self, value):
		"""
		Set current grid property. Both in the viewport and in the optionVar (if given).
		"""
		kwargs = {self.kwarg: value}
		_pm.grid(**kwargs)
		if self.optionVar:  # check that we provided an optionVar name
			_pm.optionVar[self.optionVar] = self.type(value)

	def __get_default(self):
		"""
		Gets the default value of of a grid property.
		It falls back from global variable to the low-level grid default.
		"""
		res = None
		reset = False

		if self.globalName:  # check that we provided a global variable
			try:
				glob = _pm.melGlobals[self.globalName]
			except KeyError:
				reset = True
			else:
				if issubclass(self.type, _str_t) and not glob:
					reset = True
				else:
					res = glob
				if self.optionVar:
					reset = True

		kwargs = {
			'q': True,
			'default': True,
			self.kwarg: True
		}
		default = _pm.grid(**kwargs)  # we shouldn't suppress an error if it's thrown here
		if res is None:
			res = default
			if self.optionVar or self.globalName:
				reset = True

		if reset:
			self.__set_default(res)
		return res


	def __set_default(self, value):
		if self.globalName:
			_pm.melGlobals.set(self.globalName, value, self.globalType)


# val_types = ('string', 'string[]', 'int', 'int[]', 'float', 'float[]', 'vector', 'vector[]')

enabled = _VarNames("toggle", bool, "", "", "")
size = _VarNames("size", float, "gridSize", "float", "gGridSizeDefault")
spacing = _VarNames("spacing", float, "gridSpacing", "float", "gGridSpacingDefault")
divisions = _VarNames("divisions", int, "gridDivisions", "float", "gGridDivisionsDefault")
axes = _VarNames("displayAxes", bool, "displayGridAxes", "int", "gGridDisplayAxesDefault")
axes_bold = _VarNames("displayAxesBold", bool, "displayGridAxesAccented", "int", "gGridDisplayAxesAccentedDefault")
lines = _VarNames("displayGridLines", bool, "displayGridLines", "int", "gGridDisplayGridLinesDefault")
lines_subdivision = _VarNames(
	"displayDivisionLines", bool,
	"displayDivisionLines", "int", "gGridDisplayDivisionLinesDefault"
)
labels_persp = _VarNames(
	"displayPerspectiveLabels", bool,
	"displayGridPerspLabels", "int", "gGridDisplayGridPerspLabelsDefault"
)
labels_ortho = _VarNames(
	"displayOrthographicLabels", bool,
	"displayGridOrthoLabels", "int", "gGridDisplayGridOrthoLabelsDefault"
)
labels_persp_pos = _VarNames(
	"perspectiveLabelPosition", str,
	"displayGridPerspLabelPosition", "string", "gGridDisplayPerspLabelPositionDefault"
)
labels_ortho_pos = _VarNames(
	"orthographicLabelPosition", str,
	"displayGridOrthoLabelPosition", "string", "gGridDisplayOrthoLabelPositionDefault"
)


def reset():
	_pm.grid(reset=1)


def update_option_vars():
	for prop in (
		enabled, size, spacing, divisions,
		axes, axes_bold, lines, lines_subdivision,
		labels_persp, labels_ortho, labels_persp_pos, labels_ortho_pos
	):
		prop.property_value = prop.property_value
