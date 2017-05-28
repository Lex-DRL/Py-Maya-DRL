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
	explicit_to_exr=False
).py_file_path()
print r




from for_nuke import nk_envs
nk_envs.get_src_tex(r'y:\Farm\Textures_Preprocess\_BG\Earth\earth_normalized.png')
nk_envs.get_out_tex(r'y:\Farm\Textures_Preprocess\_BG\Earth\earth_normalized.png', '', False)
nk_envs.get_nuke_exe_path(nuke_dir='', nuke_exe='')
nk_envs.get_nk_script_path(nk_dir='', nk_filename='')
nk_envs.get_py_script_path(py_dir='', py_filename='')