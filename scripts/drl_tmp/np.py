import numpy as np

src_pos = np.array([0.8, 0.6, 0.1])
# transform matrix with rot values: 20, 10, 35 (from Houdini):
m_x = np.array([0.806707, 0.564863, -0.173648])
m_y = np.array([-0.490335, 0.803816, 0.336824])
m_z = np.array([0.329841, -0.186573, 0.925417])
np.cross(m_x, m_y)
mtx = np.column_stack((m_x, m_y, m_z))  # !!! axis vectors go to columns !!!
in_world = np.matmul(mtx, src_pos)  # world pos of src point transformed with mtx

inv = np.linalg.inv(mtx)  # get local pos in mtx from world pos
pos_in_world = np.array([0.384149, 0.915523, 0.155718])  # from Houdini
pos_in_mtx_space = np.matmul(inv, pos_in_world)  # should be ~equal to src_pos

inv_cut = inv[:-1]
type(inv)
projected = np.matmul(inv_cut, pos_in_world)





def_bright = np.array([1., 1, 1])
def_color = np.array([0, 0.132934, 0.4])
color=None
bright=None


def mtx_uv_to_rgb(c=None, b=None):
	v_clr = np.array(c) if c else def_color
	v_wht = np.array(b) if b else def_bright
	v_cross = np.cross(v_clr, v_wht)
	uv_to_rgb = np.column_stack((v_clr, v_wht, v_cross))  # type: np.ndarray
	return uv_to_rgb

pt_rgb = 0.1 * def_color + 0.7 * def_bright
pt_uv = np.array([0.1, 0.7])
mtx = mtx_uv_to_rgb()
mtx_cut = mtx.transpose()[:-1].transpose()
np.matmul(mtx_cut, pt_uv)