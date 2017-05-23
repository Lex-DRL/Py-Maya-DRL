res = []
for item in pm.resourceManager(nameFilter='*'):
	try:
		#Make sure the folder exists before attempting.
		pm.resourceManager(saveAs=(item, "E:/5-Internet/Dropbox/0-Settings/Maya/2014-x64/_default_icons/{0}".format(item)))
	except:
		#For the cases in which some files do not work for windows, name formatting wise. I'm looking at you 'http:'!
		res.append(item)