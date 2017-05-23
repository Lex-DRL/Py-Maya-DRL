from drl import obj
import pprint
reload(obj)
qqq = obj.batchImpMB('E:/1-Projects/Maya/z-Slasher/Scenes/Zbrush/Lighting/forBake')
www = obj.zbExp(path=r'E:\0-Projects\z-Slasher\Scenes\Zbrush\0-Level\Bridge\z-UV_exchange')
res = obj.batchExp(path='E:/0-Projects/z-Slasher/Scenes/Zbrush/0-Level/Bridge/z-UV_exchange/www/',
	toDash=False,
	
)
pprint.pprint(qqq)

for w in www:
	print w


import maya.cmds as cmds
connectDest = cmds.ls(sl=True)
attr = ['mainColor_color', 'MSA_float', 'SampleBase_float', 'ConeAngle_float', 'Kind_float', 'MaxDist_float']
'''
attr = {'Kind_float':'Kind_float'}
srcAttr = attr.keys()
'''
if len(connectDest) > 1 and attr:
	connectSrc = connectDest.pop(0)
	for o in connectDest:
		'''
		for a in srcAttr:
			cmds.connectAttr(connectSrc+'.'+a, o+'.'+attr[a], f=True)
		'''
		for a in attr:
			cmds.connectAttr(connectSrc+'.'+a, o+'.'+a, f=True)