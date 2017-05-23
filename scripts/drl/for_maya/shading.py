__author__ = 'DRL'

from maya import cmds

def thumb_switch(mode=2):
	'''
	Allows to switch thumbnails in AE on and off.
	:param mode:
		0 - turn OFF
		1 - turn ON
		else - Toggle
	:return: None
	'''
	def on():
		cmds.renderThumbnailUpdate(True)
		print 'Thumbnail ON'
	def off():
		cmds.renderThumbnailUpdate(False)
		print 'Thumbnail OFF'
	def switch():
		if cmds.renderThumbnailUpdate(q=1):
			off()
		else:
			on()

	if mode > 1 or mode < 0:
		mode = 2
	options = {
		0: off,
		1: on,
		2: switch
	}

	options[mode]()