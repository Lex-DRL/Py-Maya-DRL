__author__ = 'DRL'

import os

from maya import cmds
import drl_common.errors as err

_str_types = (str, unicode)


def get_maya_app_dir():
	"""
	Returns the location of Maya settings folder.
	"""
	if 'MAYA_APP_DIR' in os.environ:
		return os.environ['MAYA_APP_DIR']

	home = os.environ.get('HOME', None)
	if not home:
		home = os.path.expanduser("~")
	home = os.path.join(home, 'maya').replace('\\', '/')
	assert isinstance(home, _str_types)
	return home


def get_project_dir():
	res = cmds.workspace(q=True, rootDirectory=True)
	assert isinstance(res, _str_types)
	return res


def is_ple():
	"""
	Is it an eval version of Maya?

	:return: <bool> True if it's Maya PLE. False if it's a complete Maya.
	"""
	res = cmds.about(evalVersion=1)
	if not isinstance(res, bool):
		res = bool(res)
	assert isinstance(res, bool)
	return res