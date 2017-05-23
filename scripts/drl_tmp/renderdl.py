__author__ = 'DRL'

import os
from subprocess import call

folder = r'E:\1-Projects\Maya\ssTrapsSrc\3delight\_ToRender\rib'
delight = r'C:\Program Files\3Delight\bin\renderdl.exe'
files = os.listdir(folder)
files = [os.path.join(folder, x) for x in files]
ribs = [x for x in files if os.path.isfile(x) and os.path.splitext(x)[-1].lower() == '.rib']
ribs.sort()

for r in ribs:
	# r = ribs[0]
	cmdArgs = [
		delight,
		'-p', '0',
		'-P', '0',
		'-nd', '-progress',
		r
	]
	call(cmdArgs)