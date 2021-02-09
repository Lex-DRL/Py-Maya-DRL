__author__ = 'Lex Darlog (DRL)'

# from maya import cmds
# from drl_common import errors as err
#
#
# __types = (int, float)
# __str_types = (str, unicode)
#
#
# def start(
# 	message='', title='Progress',
# 	interruptable=True,
# 	min=0, max=100, start_value=0
# ):
# 	end()
# 	cmds.progressWindow(
# 		title=title, status=message,
# 		isInterruptable=interruptable,
# 		min=min, max=max, progress=start_value
# 	)
#
#
#
# def is_cancelled():
# 	"""
# 	Returns true if the user has tried to cancel the operation.
# 	Returns false otherwise.
# 	"""
# 	res = cmds.progressWindow(q=True, isCancelled=True)
# 	assert isinstance(res, bool)
# 	if res:
# 		end()
# 	return res
#
#
# def is_active():
# 	"""
# 	This is supposed to be used as the condition for <while> loop.
# 	Returns true if the progress still didn't reach the end.
# 	Also closes the progress window when it's done.
#
# 	:return: bool
# 	"""
# 	going = progress_get() < max_get() and not is_cancelled()
# 	if not going:
# 		end()
# 	return going
#
#
# def interruptable_get():
# 	"""
# 	Returns true if the progress window should respond
# 	to attempts to cancel the operation.
#
# 	The cancel button is disabled if this is set to true.
# 	"""
# 	res = cmds.progressWindow(q=True, isInterruptable=True)
# 	assert isinstance(res, bool)
# 	return res
#
#
# def interruptable_set(val):
# 	err.WrongTypeError.raise_if_needed(val, bool, 'is-interruptable value')
# 	cmds.progressWindow(e=True, isInterruptable=val)
#
#
# def progress_get():
# 	"""
# 	The amount of progress currently shown on the control.
#
# 	The value will always be between min and max.
#
# 	Default is equal to the minimum when the control is created.
# 	:return:
# 	"""
# 	res = cmds.progressWindow(q=True, progress=True)
# 	assert isinstance(res, __types)
# 	return res
#
#
# def progress_set(val):
# 	err.WrongTypeError.raise_if_needed(val, __types, 'progress value')
# 	cmds.progressWindow(e=True, progress=val)
# 	if val > max_get():
# 		end()
#
#
# def increment(amount=1):
# 	err.WrongTypeError.raise_if_needed(amount, __types, 'amount')
# 	cmds.progressWindow(e=True, step=amount)
# 	if (progress_get() + amount) > max_get():
# 		end()
#
#
# def min_get():
# 	res = cmds.progressWindow(q=True, min=True)
# 	assert isinstance(res, __types)
# 	return res
#
#
# def min_set(val):
# 	err.WrongTypeError.raise_if_needed(val, __types, 'min value')
# 	cmds.progressWindow(e=True, min=val)
#
#
# def max_get():
# 	res = cmds.progressWindow(q=True, max=True)
# 	assert isinstance(res, __types)
# 	return res
#
#
# def max_set(val):
# 	err.WrongTypeError.raise_if_needed(val, __types, 'min value')
# 	cmds.progressWindow(e=True, max=val)
#
#
# def title_get():
# 	res = cmds.progressWindow(q=True, title=True)
# 	assert isinstance(res, __str_types)
# 	return res
#
#
# def title_set(val):
# 	err.WrongTypeError.raise_if_needed(val, __str_types, 'title name')
# 	cmds.progressWindow(e=True, title=val)
#
#
# def message_get():
# 	res = cmds.progressWindow(q=True, status=True)
# 	assert isinstance(res, __str_types)
# 	return res
#
#
# def message_set(val):
# 	err.WrongTypeError.raise_if_needed(val, __str_types, 'status message')
# 	cmds.progressWindow(e=True, status=val)
#
#
# def end():
# 	cmds.progressWindow(endProgress=True)
# 	progress_set(max_get())