from drl.aivik import export as e
reload(e)
e.IslandsPVE().del_trees_mesh().del_enemy_base_mesh().combine_islands_dn().combine_waterfalls()




from drl.for_maya.plugins import fbx
reload(fbx)
fbx.FBX().presets_path()

fbx.BatchExporter(r'e:\1-Projects\0-Common_Code').load_preset('AIVIK-Geo').add_selected_groups().export_all_groups()

from drl.aivik import export_old
export_old.self == export_old


from os import path
p = r'y:\Farm\Textures_Preprocess\_Ramps\0-src\00-ramp-UI-1.png'
path.splitext(r'y:\Farm\Textures_Preprocess\_Ramps\0-s.rc\.00-ramp-UI-1png')

from for_nuke import processor as pr
reload(pr)

r = pr.NukeProcessor(
	(
		r'y:\Farm\Textures_Preprocess\_BG\Earth\earth_normalized.png',
		r'y:\Farm\Textures_Preprocess\_BG\Earth\earth_2-height.png'
	),
	# (r'y:\Farm\Textures_Preprocess\_Ramps\0-src\00-ramp-UI-1.exr', None),
	explicit_to_exr=False,
	nk_dir=r'e:\1-Projects\0-Scripts\Python\for_nuke',
	py_dir=r'e:\1-Projects\0-Scripts\Python\for_nuke'
)
r.get_command()
print r.get_command()
nuke_exe_path = r.nuke_exe_path()
nuke_x = 0
py_path = r.py_file_path()
nk_path = r.nk_file_path()
src_tex = r.src_tex
out_tex = r.get_out_tex()
cmd = '"{nuke}" {nukex} -t "{py}" "{nk}" {src} "{out}"'.format(
	nuke=nuke_exe_path,
	nukex='--nukex' if nuke_x else '',
	py=py_path,
	nk=nk_path,
	src=repr(str(src_tex)),
	out=repr(str(out_tex))
)
print cmd

str(r.src_tex)
q = str(
	(
		unicode(r'y:\Farm\Textures_Preprocess\_BG\Earth\earth_normalized.png'),
		unicode(r'y:\Farm\Textures_Preprocess\_BG\Earth\earth_2-height.png')
	)
)
print(repr(q))




from for_nuke import nk_envs
nk_envs.get_src_tex(r'y:\Farm\Textures_Preprocess\_BG\Earth\earth_normalized.png')
nk_envs.get_out_tex(r'y:\Farm\Textures_Preprocess\_BG\Earth\earth_normalized.png', '', False)
nk_envs.get_nuke_exe_path(nuke_dir='', nuke_exe='')
nk_envs.get_nk_script_path(nk_dir='', nk_filename='')


nk_envs.get_py_script_path(py_dir='', py_filename='')
nuke_exe = nk_envs.get_nuke_exe_path(nuke_dir='', nuke_exe='')

nk_envs.get_py_script_path(py_dir='', py_filename='')
print nuke_exe


import _winreg as reg
from pprint import pprint as pp

root = reg.OpenKey(reg.HKEY_CLASSES_ROOT, r'Installer\Assemblies', 0, reg.KEY_ALL_ACCESS)
subs = [
	k for k in (reg.EnumKey(root, i) for i in xrange(reg.QueryInfoKey(root)[0]))
	if k.startswith(r'C:|Program Files|Common Files|Microsoft Shared|Team Foundation Server|14.0')
]
pp(subs)
reg.DeleteKeyEx(root, subs[0])
pp([
	reg.DeleteKeyEx(root, k) for k in subs
])
