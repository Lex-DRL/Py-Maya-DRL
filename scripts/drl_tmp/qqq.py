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






import matplotlib.pyplot as plt
import numpy as np

t = np.arange(0.0, 2.0, 0.01)
t = [x * 0.1 for x in xrange(10)]
s = [(x * 13) % 3.0 for x in t]
s = 1 + np.sin(2*np.pi*t)
plt.plot(t, s)

plt.xlabel('time (s)')
plt.ylabel('voltage (mV)')
plt.title('About as simple as it gets, folks')
plt.grid(True)
plt.savefig("test.png")
plt.show()

from os import path
path.abspath('.')


import mining_graph as m
reload(m)
from pprint import pprint as pp
from datetime import timedelta as td
pp(m.parse_log_files(hash_rate=True, gpu=False))
m.display_graph(max_timedelta=td(days=1, hours=0), hash_rate=True, gpu_temp=True, gpu_fan=True)
m.display_graph(hash_rate=True, gpu_temp=True, gpu_fan=True)


a = '215.4'
float(a)

"""
Compute the coherence of two signals
"""
import numpy as np
import matplotlib.pyplot as plt

# make a little extra space between the subplots
plt.subplots_adjust(wspace=0.5)

dt = 0.01
t = np.arange(0, 30, dt)
nse1 = np.random.randn(len(t))                 # white noise 1
nse2 = np.random.randn(len(t))                 # white noise 2
r = np.exp(-t/0.05)

cnse1 = np.convolve(nse1, r, mode='same')*dt   # colored noise 1
cnse2 = np.convolve(nse2, r, mode='same')*dt   # colored noise 2

# two signals with a coherent part and a random part
s1 = 0.01*np.sin(2*np.pi*10*t) + cnse1
s2 = 0.01*np.sin(2*np.pi*10*t) + cnse2

plt.subplot(311)
plt.plot(t, s1, t, s2)
plt.xlim(0, 5)
plt.xlabel('time')
plt.ylabel('s1 and s2')
plt.grid(True)

plt.subplot(312)
cxy, f = plt.cohere(s1, s2, 256, 1./dt)
plt.ylabel('coherence')
plt.show()
plt.ticklabel_format




"""
===============================
Legend using pre-defined labels
===============================

Notice how the legend labels are defined with the plots!
"""


import numpy as np
import matplotlib.pyplot as plt

# Make some fake data.
a = b = np.arange(0, 3, .02)
c = np.exp(a)
d = c[::-1]

# Create plots with pre-defined labels.
fig, ax = plt.subplots()
ax.plot(a, c, 'k--', label='Model length')
ax.plot(a, d, 'k:', label='Data length')
ax.plot(a, c + d, 'k', label='Total message length')

legend = ax.legend(loc='upper center', shadow=True, fontsize='x-large')

# Put a nicer background color on the legend.
legend.get_frame().set_facecolor('#00FFCC')

plt.show()
