__author__ = 'Lex Darlog (DRL)'

from collections import defaultdict
from pymel import core as pm
from drl_common.py_2_3 import (
	xrange as _xrange,
)
from drl.for_maya.ls import pymel as ls

try:
	from typing import Dict, List, Set, Tuple
except ImportError:
	pass


def del_cv(items=None, selection_if_none=True):
	"""
	Safe-deletion of curve CVs. I.e., this deletion doesn't mess up with
	a curve's "multiple end knots" state,
	nor creates extra CVs when they're deleted at the ends of curve.

	Unfortunately, it does override the knot values (i.e., parametrization).
	But there's no simple way to detect whether it needs to be overridden or not.
	"""
	items = ls.default_input.handle_input(items, selection_if_none, flatten=False)
	items = filter(
		lambda x: isinstance(x, pm.NurbsCurveCV),
		items
	)
	if not items:
		return
	cvs_by_shape = defaultdict(list)  # type: Dict[str, List[pm.NurbsCurveCV]]
	for itm in items:
		nm = ls.long_item_name(itm, keep_comp=False)
		cvs_by_shape[nm].append(itm)

	def del_single_curve_cvs(
		deleted_cvs  # type: List[pm.NurbsCurveCV]
	):
		"""
		Re-create a single curve, removing the given UVs.
		It's expected that the provided list is not empty
		and it contains CVs of the same curve.
		"""
		curve = deleted_cvs[0].node()  # type: pm.nt.NurbsCurve
		form = curve.form()
		is_closed = form in (
			pm.nt.NurbsCurve.Form.closed,
			pm.nt.NurbsCurve.Form.periodic
		)
		degree = curve.degree()
		deleted_cvs = pm.ls(deleted_cvs, fl=1)  # type: List[pm.NurbsCurveCV]
		num_removed = len(deleted_cvs)
		curr_cvs = curve.cv  # type: pm.NurbsCurveCV
		num_kept = len(curr_cvs) - num_removed
		# error-check:
		if num_kept < (degree + 1):
			raise ValueError(
				"{crv}:\nCan't remove {rem} CVs because then the curve will have {kept} CVs with degree: {deg}".format(
					crv=ls.long_item_name(curve, keep_comp=False),
					rem=num_removed,
					kept=num_kept,
					deg=degree
				)
			)

		# if is_closed:
		# 	# open the curve as the 1st step:
		# 	pm.closeCurve(curve, ch=0, preserveShape=0, replaceOriginal=1)

		# set of removed CVs' indices:
		del_cv_ids = set(
			cv.index() for cv in deleted_cvs
		)  # type: Set[int]

		# prepare new curve points:
		new_cvs_pos = [
			tuple(cv.getPosition())
			for cv in curr_cvs
			if cv.index() not in del_cv_ids
		]  # type: List[Tuple[float]]
		if is_closed:
			# for the closed curve, the last N points need to match to the first N pts,
			# where N is degree
			new_cvs_pos += new_cvs_pos[:degree]
		new_knots = (
			[-float(u) for u in _xrange(degree - 1, 0, -1)] +  # [..., -2.0, -1.0], from degree
			[float(u) for u in _xrange(len(new_cvs_pos))]  # [0.0, 1.0, 2.0, ...], from CVs count
		)

		# the main curve re-creation
		pm.curve(
			curve,
			replace=1,
			point=new_cvs_pos,
			knot=new_knots,
			periodic=is_closed
		)
		# curve = pm.closeCurve(curve, ch=0, preserveShape=0, replaceOriginal=1)
		return curve

	return [del_single_curve_cvs(cvs) for cvs in cvs_by_shape.values()]
