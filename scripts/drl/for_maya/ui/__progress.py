__author__ = 'DRL'

from pymel.core import uitypes as _ui


class Progress(object):
	def __init__(self, max_displayed=3):
		super(Progress, self).__init__()
		self.__get_progresses()  # ensuring the class has private processes list

		self.max_displayed = max_displayed
		self.__bars = tuple()
		self.__is_main = False

	def __get_progresses(self):
		"""
		On the current class (including inherited), creates <__progresses_list>
		if it doesn't exist yet, and returns it.

		:return: <list>
		"""
		try:
			return self.__class__.__progresses_list
		except AttributeError:
			nu = []
			self.__class__.__progresses_list = nu
			return nu

	@property
	def __progresses(self):
		"""
		Raw list, for low-level access ONLY.

		It has setter, too. So it allows to modify the list itself,
		and you need to be so be **EXTREMELY CAUTIOUS** with it.
		"""
		return self.__get_progresses()

	@__progresses.setter
	def __progresses(self, value):
		self.__class__.__progresses_list = value

	@property
	def progresses(self):
		return tuple(self.__get_progresses())

	@property
	def is_main(self):
		return self.__is_main

	@property
	def bars(self):
		"""
		Tuple of **pymel.core.uitypes.MainProgressBar** UI items
		the current progress is displayed in.

		It's tuple for the case of the main progress displayed simultaneously
		in the status bar and the multi-progress window.
		"""
		return self.__bars

	@bars.setter
	def bars(self, value):
		self.__bars = value



	def start(self):
		"""
		Prepare UI for current process and add it to the global progresses list.
		"""
		pr = self.__get_progresses()
		if not(self in pr):
			pr.append(self)
		self.__is_main = (pr.index(self) == 0)
		self.__begin()

	def __begin(self):
		"""
		Prepare UI for current process.
		But don't touch the global progresses list.
		"""
		pass

	def end(self):
		"""
		Finish current progress and all of it's children. Remove them from progresses list.
		If they're not completed, interrupt them.
		"""
		pr = self.__progresses
		if not(self in pr):
			self.__interrupt()
			return

		i = pr.index(self)
		removed = pr[i:]  # all the preceding progresses before current
		left = pr[:i]  # current progress and all the rest
		for p in removed:
			p.__interrupt()
		self.__progresses = left

	def __interrupt(self):
		"""
		Interrupt current process. I.e., remove any UI elements
		and stop the working process.
		But don't touch the global progresses list.
		"""
		pass