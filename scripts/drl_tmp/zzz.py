from drl.for_unity import bake as bk
reload(bk)
bk.Sequence.render_bake_set_frame()
bk.Prepare()





from collections import defaultdict
d = defaultdict(list)
d.keys()
d['aaa'].append(123)

grp = {}
grp['aaa'] = 123
grp.keys()