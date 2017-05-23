# coding=utf-8
__author__ = 'DRL'

import os
from pymel import core as pm
from drl_common import errors as err


class PluginBaseError(Exception):
	"""
	Base class for any errors related to <Plugin> class.
	"""
	def __init__(self, plugin):
		"""
		Base class for any errors related to <Plugin> class.

		:param plugin: <str> plugin name or path.
		"""
		formatter = 'Error in plugin <%s>'
		if not isinstance(plugin, (str, unicode)):
			plugin = str(plugin)
		msg = formatter % plugin
		super(PluginBaseError, self).__init__(msg)
		self._msg_formatter = formatter
		self._plugin = plugin

	def _construct_message(self):
		"""
		Private method which generates message.

		Instead of overriding this method, you may want to change the value of self._msg_formatter.

		:return: <str> generated message.
		"""
		return self._msg_formatter % self._plugin

	def _update_message(self):
		"""
		Private method for updating the message.
		You need to call it in constructor, after you reset self._msg_formatter.
		"""
		self.message = self._construct_message()

	def _set_plugin(self, plugin):
		"""
		Private method re-setting the plugin name/path.

		:param plugin: <str> plugin name or path.
		"""
		if not isinstance(plugin, (str, unicode)):
			plugin = str(plugin)
		self._plugin = plugin
		self._update_message()

	@property
	def plugin(self):
		"""
		Plugin name or path
		"""
		return self._plugin

	@plugin.setter
	def plugin(self, value):
		self._set_plugin(value)


class PluginNotRegisteredError(PluginBaseError):
	def __init__(self, plugin):
		super(PluginNotRegisteredError, self).__init__(plugin)
		self._msg_formatter = 'Plugin not registered: <%s>'
		self._update_message()


class PluginNotLoadedError(PluginBaseError):
	def __init__(self, plugin):
		super(PluginNotLoadedError, self).__init__(plugin)
		self._msg_formatter = 'Plugin not loaded: <%s>'
		self._update_message()


# -----------------------------------------------------------------------------


class Plugin(object):
	"""
	A high-level class allowing to load/unload a plugin and gather it's info.

	The constructor takes exactly one string argument: either a plugin name or it's full path.
	"""
	def __init__(self, plugin):
		super(Plugin, self).__init__()
		self.__name = ''
		self.__path = ''
		self.__id = ''
		self.__set_plugin(plugin)

	def __set_plugin(self, plugin):
		plugin = err.NotStringError(plugin, 'plugin').raise_if_needed()
		plugin = plugin.replace('\\', '/').rstrip('/')
		self.__name = ''
		self.__path = ''
		self.__id = ''
		split_plugin = plugin.split('/')
		if len(split_plugin) > 1:
			self.__path = plugin
			self.__name = os.path.splitext(split_plugin[-1])[0]
			self.__id = plugin
		else:
			self.__name = os.path.splitext(plugin)[0]
			self.__id = self.__name

	def set_plugin(self, plugin):
		self.__set_plugin(plugin)
		return self

	@property
	def name(self):
		"""
		Name of the plugin (read-only).

		To change the plugin, use set_plugin() method instead.
		"""
		return self.__name

	@property
	def path(self):
		"""
		The path to the plugin.

		If the plugin was set via just name, and no such plugin is registered, an exception will be thrown.

		To change the plugin, use set_plugin() method instead.
		"""
		path = self.__path
		if path:
			return path
		name = self.__name
		if not Plugin.__registered(name):
			raise self.__not_registered_error()
		path = pm.pluginInfo(name, q=1, path=1)
		self.__path = path
		self.__id = path
		return path

	@property
	def id(self):
		"""
		Either path or name of the plugin - depending on what's known.

		Path if it's available, name otherwise.
		"""
		return self.__id

	@staticmethod
	def __registered(plugin):
		return pm.pluginInfo(plugin, q=1, registered=1)

	def __not_registered_error(self):
		return PluginNotRegisteredError(self.__id)

	def registered(self):
		"""
		Whether the current plugin is registered in Maya.
		A plugin becomes registered when it's first loaded.
		"""
		return Plugin.__registered(self.__id)

	def error_if_not_registered(self, try_to_load_instead_of_error=False):
		"""
		Throws an error if a given plugin doesn't exist in Maya.
		"""
		if not self.registered():
			if try_to_load_instead_of_error:
				self.load()
			else:
				raise self.__not_registered_error()
		return self

	def loaded(self):
		"""
		Returns a boolean specifying whether or not the plugin is loaded.

		:return: <bool>
		"""
		return pm.pluginInfo(self.__id, q=1, loaded=1)

	def error_if_not_loaded(self):
		"""
		Throws an error if the plugin isn't loaded.
		"""
		if not self.loaded():
			raise PluginNotLoadedError(self.__id)
		return self

	def version(self, load_if_not_registered=False):
		"""
		Returns a string containing the version the plugin.

		:param load_if_not_registered: if True and the plugin isn't found, try to load it first, instead of throwing an error.
		:return: <str>
		"""
		self.error_if_not_registered(load_if_not_registered)
		return pm.pluginInfo(self.__id, q=1, version=1)

	def load(self, quiet=False, user_name=None):
		"""
		Loads the plugin.

		:param quiet: <bool> Don't print a warning if you attempt to load a plug-in that is already loaded.
		:param user_name: <string> Set a user defined name for the plug-ins that are loaded. If the name is already taken, then a number will be added to the end of the name to make it unique.
		"""
		kwargs = dict()
		if quiet:
			kwargs['quiet'] = True
		if user_name:
			err.NotStringError(user_name, 'user_name').raise_if_needed()
			kwargs['name'] = user_name
		pm.loadPlugin(self.__id, **kwargs)
		return self

	def defined_node_types(self, load_if_not_registered=False):
		"""
		Returns the defined node types names as a list of strings.

		:param load_if_not_registered: to get this list, the given plugin needs to be registered. If True, it will be loaded (if not yet). Otherwise, error may be thrown.
		:return: <list> of strings.
		"""
		self.error_if_not_registered(load_if_not_registered)
		return pm.pluginInfo(self.__id, q=1, dependNode=1)

	def unload(self, remove_dependent_nodes=False):
		"""
		Allows to easier unload a given Maya plugin.

		:param remove_dependent_nodes: if True, all the dependent nodes will be removed from the scene, so the scene will no longer require this plugin.
		:return: names of removed nodes in <remove_dependent_nodes> mode, None otherwise.
		"""
		self.error_if_not_registered()

		if not self.loaded():
			return

		if not remove_dependent_nodes:
			pm.unloadPlugin(self.__id, force=1)
			return

		node_types = self.defined_node_types()
		nodes = pm.ls(type=node_types) if node_types else []
		pm.unloadPlugin(self.__id, force=1)
		if not nodes:
			return

		lock_states = pm.lockNode(nodes, q=1, lock=1)
		locked_nodes = [n for n, locked in zip(nodes, lock_states) if locked]
		if locked_nodes:
			pm.lockNode(locked_nodes, lock=0)

		names = [x.name() for x in nodes]
		pm.delete(nodes)
		return names
