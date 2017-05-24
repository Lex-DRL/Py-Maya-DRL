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

r = pr.NukeProcessor(
	(
		r'y:\Farm\Textures_Preprocess\_Ramps\0-src\00-ramp-UI-1.png',
		r'y:\Farm\Textures_Preprocess\_Ramps\0-src\01-gradient-orange.png',
	),
	# (r'y:\Farm\Textures_Preprocess\_Ramps\0-src\00-ramp-UI-1.exr', None),
	explicit_to_exr=False
).get_out_tex()