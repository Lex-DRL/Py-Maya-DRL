import drl_user_buttons as drl_btn
drl_btn.cleanup.skip_shapes()


from drl.aivik import export as e
reload(e)
exporter = e.IslandsPVE()
exporter.del_trees_mesh().del_enemy_base_mesh()
exporter.combine_islands_dn().combine_waterfalls()


from drl.for_maya.plugins import fbx
reload(fbx)
fbx.FBX().presets_path()
exporter = fbx.BatchExporter(r'e:\1-Projects\0-Common_Code')
exporter.load_preset('AIVIK-Geo').add_selected_groups().export_all_groups()


from drl_common.srgb import linear_to_srgb
linear_to_srgb(0.5)


from drl.for_maya.ls.convert.components import Poly
Poly().to_vertex_faces()

from drl.for_maya.auto.cleanup import UVSetsRule as Rule
Rule('LM_color').kept_sets_for_object()

from drl.for_maya.auto import BakedToUVs
BakedToUVs().transfer()


drl_btn.curves.del_cv()