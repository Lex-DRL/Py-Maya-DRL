from math import floor


def common_period(in_periods, threshold=0.00000000001):
	cur_period = 0
	still_seeking = True
	x = in_periods[0]
	periods_compare = in_periods[1:]
	deltas = tuple()
	cur_repeats = tuple()
	while still_seeking:
		cur_period += 1
		cur_x = x * cur_period
		cur_repeats = tuple(int(floor(cur_x / y) + 0.1) for y in periods_compare)
		cur_vars = tuple(p * y for p, y in zip(cur_repeats, periods_compare))
		deltas = tuple(abs(y - cur_x) for y in cur_vars)
		if all(dl <= threshold for dl in deltas):
			still_seeking = False
	return tuple([cur_period] + list(cur_repeats)), deltas, in_periods


common_period([
	1.0 / x for x in (  # <- periods; frequencies:
		1.0,
		1.73,
		4.79,
		9.11,
		0.29
	)
])
