__author__ = 'DRL'

from drl_common import errors as _err

MAT_SURF = 'surfaceShader'
MAT_VOL = 'volumeShader'
MAT_DISP = 'displacementShader'

MR_MAT = 'miMaterialShader'
MR_SHADOW = 'miShadowShader'

MR_VOL = 'miVolumeShader'
MR_PHOT = 'miPhotonShader'
MR_PHOT_VOL = 'miPhotonVolumeShader'
MR_DISP = 'miDisplacementShader'
MR_ENV = 'miEnvironmentShader'
MR_LM = 'miLightMapShader'
MR_CONTOUR = 'miContourShader'

__maya_attrs = (MAT_SURF, MAT_VOL, MAT_DISP)
__mr_attrs = (
	MR_MAT,
	MR_SHADOW,

	MR_VOL,
	MR_PHOT,
	MR_PHOT_VOL,
	MR_DISP,
	MR_ENV,
	MR_LM,
	MR_CONTOUR
)
__fallbackable = (
	MAT_SURF, MAT_VOL, MAT_DISP,
	MR_MAT, MR_VOL, MR_DISP
)
__fallbacks = {
	MAT_SURF: MR_MAT,
	MAT_VOL: MR_VOL,
	MAT_DISP: MR_DISP,
	MR_MAT: MAT_SURF,
	MR_VOL: MAT_VOL,
	MR_DISP: MAT_DISP
}


def is_maya(attr_nm):
	return (
		_err.NotStringError(attr_nm, 'attr_nm').raise_if_needed_or_empty()
		in __maya_attrs
	)


def is_mr(attr_nm):
	return (
		_err.NotStringError(attr_nm, 'attr_nm').raise_if_needed_or_empty()
		in __mr_attrs
	)


def has_fallback(attr_nm):
	return (
		_err.NotStringError(attr_nm, 'attr_nm').raise_if_needed_or_empty()
		in __fallbackable
	)


def fallback(attr_nm):
	if not has_fallback(attr_nm):
		return None
	return __fallbacks[attr_nm]


def fallback_conditionally(attr_nm, from_mr=True, to_mr=False):
	do_fall = False
	if is_maya(attr_nm):
		do_fall = to_mr
	elif is_mr(attr_nm):
		do_fall = from_mr

	if do_fall:
		return fallback(attr_nm)
	return None