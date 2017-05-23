from drl.aivik import export as e
reload(e)
e.IslandsPVE().del_trees_mesh().del_enemy_base_mesh().combine_islands_dn().combine_waterfalls()




from drl.for_maya.plugins import fbx
reload(fbx)
fbx.FBX().presets_path()

fbx.BatchExporter(r'e:\1-Projects\0-Common_Code').load_preset('AIVIK-Geo').add_selected_groups().export_all_groups()

from drl.aivik import export_old
export_old.self == export_old


from drl import aivik
reload(aivik)
aivik.update_duplicated.meshes()

from drl.aivik import export
export.BaseExport().export_as_asset_static()
export.IslandsPVE().export_as_pve_islands()



from drl.for_maya.auto import cleanup as cl
reload(cl)
cl.cleanup_all(rename_shapes=False)


aaa = ['a', 'b', 'c', '']
aaa = tuple(aaa)
all(isinstance(x, (str, unicode)) for x in aaa)



aaa = tuple(' '.join([x, 'Yo!']) for x in aaa)

rule = ((1,),)
type(rule)
len(rule[0])


' Got: {0}.'.format(rule.__repr__())
a = ('zzz', 'qqq')
b = [1, 2, 3]
b.extend(a)


def qqq():
	return NotImplemented

try:
	qqq()
	print 'AAAAA'
except NotImplementedError:
	print 'BBBBB'

from drl.for_maya.auto.cleanup import uv_sets
uv_sets.UVSets(None, ('aaa')).remove_extra_sets()



from drl.aivik import export as e
reload(e)
exp = e.IslandsPVE()
exp.del_object_sets().del_trees_mesh().del_enemy_base_mesh().del_not_exported()
exp.combine_islands_dn().combine_waterfalls()
exp.cleanup_uv_sets((1, ('LM_out', 'LM'), 'windUVs')).cleanup_color_sets()
exp.un_parent().del_not_exported()


from drl.for_maya.auto import cleanup as cl
cl.rename_all_shapes()

cl.materials.all_faces_to_shape()

from pprint import pprint as pp
from for_nuke import nk_envs
q = nk_envs.get_nuke_process_command(
	r'e:\1-Projects\0-Common_Code\Sources\Unity\DRL_Farm\Shaders\GUI\ClanIcon.shader',
	r'e:\1-Projects\0-Common_Code\Sources\Unity\DRL_Farm\Shaders\GUI\ClanIcon.qqq',
)
pp(q)