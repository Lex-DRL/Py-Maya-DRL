__author__ = 'Lex Darlog (DRL)'

import os
from maya import cmds
from pymel import core as _pm


def smd_files_axis_reorient_dialog():
	options = (
		"Model > Y-up",
		"Model > Z-up",
		"World > Y-up",
		"World > Z-up",
		"No Change"
	)
	results = {
		options[0]: 1,
		options[1]: 2,
		options[2]: 3,
		options[3]: 4
	}
	str_option = cmds.confirmDialog(
		title="SMD import options",
		message=(
			"Choose 'model' options to re-orient the imported model.\n"
			"Choose 'world' to change Maya's coordinate system."
		),
		button=options,
		defaultButton=options[0],
		cancelButton=options[4],
		dismissString=options[4]
	)
	try:
		return results[str_option]
	except KeyError:
		return 0


def read_smd_files():
	from maya import mel as maya_mel
	maya_mel.eval("source smdRead.mel;")
	from pymel.core import mel
	smds = cmds.fileDialog2(caption="Select SMD files", fileFilter="Source Model files (*.smd)", fileMode=4)
	if not smds:
		return list()
	axis_mode = smd_files_axis_reorient_dialog()
	res = list()
	for smd in smds:
		cmds.file(f=1, new=1)
		print(mel.smdRead(smd, 0, axis_mode))
		_pm.select(cl=1)
		maya_file = (os.path.splitext(smd)[0] + '.mb').replace("\\", '/')
		cmds.file(rename=maya_file)
		maya_file = cmds.file(force=1, save=1, options="v=0;", type="mayaBinary")
		res.append(maya_file)
		print("Exported scene:\n%s\n\n\n" % maya_file)
	return res
