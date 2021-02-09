__author__ = 'Lex Darlog (DRL)'

from drl.for_maya import auto as _a


def baked_to_uvs():
	return _a.BakedToUVs(srgb=True).transfer()


def explode():
	return _a.ExplodeParts().offset()
