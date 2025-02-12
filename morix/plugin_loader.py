"""
Module for loading plugins in the Morix project.

This module defines the PluginLoader class that scans the plugins directory,
loads plugin modules, and initializes them.
"""

import os
import importlib.util
import logging
from .plugins.plugin_interface import PluginInterface
from .settings import config

logger = logging.getLogger(__name__)

class PluginLoader:
    def __init__(self):
        """
        Initializes the PluginLoader.
        Initializes the PluginLoader with the specified plugin directory and an empty list of plugins.
        """
        self.plugin_directory = config.plugins_path
        self.plugins = []

    def load_plugins(self):
        """
        Loads all plugins from the plugin directory.
        Scans the plugin directory for Python files (excluding __init__.py) and loads each plugin.
        """
        try:
            plugin_files = [f for f in os.listdir(self.plugin_directory) if f.endswith('.py') and f != '__init__.py']
        except FileNotFoundError:
            logger.debug(f"Plugin directory {self.plugin_directory} not found.")
            return
        for plugin_file in plugin_files:
            self._load_plugin(plugin_file)

    def _load_plugin(self, plugin_file):
        """
        Loads a single plugin from the provided file.
        Attempts to load a plugin module from the specified file and initialize it.

        Args:
            plugin_file (str): The filename of the plugin file to load.
        """
        plugin_path = os.path.join(self.plugin_directory, plugin_file)
        module_name = os.path.splitext(plugin_file)[0]
        try:
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self._initialize_plugin(module, module_name)
        except Exception as e:
            logger.error(f"Failed to load plugin {module_name}: {e}")

    def _initialize_plugin(self, module, module_name):
        """
        Initializes a plugin module by instantiating its main class.
        Iterates through the module's attributes to find a subclass of PluginInterface (excluding PluginInterface itself),
        creates an instance, calls its initialize method, and stores it in the plugins list.

        Args:
            module: The module object of the plugin.
            module_name (str): The name of the plugin module.
        """
        for attribute_name in dir(module):
            attribute = getattr(module, attribute_name)
            if isinstance(attribute, type) and issubclass(attribute, PluginInterface) and attribute is not PluginInterface:
                plugin_instance = attribute()
                plugin_instance.initialize()
                self.plugins.append(plugin_instance)
                logger.info(f"Plugin {module_name} loaded and initialized.")

    def execute_plugin_function(self, function_name, args):
        """
        Executes a specified function on all loaded plugins.

        Args:
            function_name (str): The name of the function to execute.
            args (dict): The arguments to pass to the function.

        Returns:
            list: A list of results from each plugin that has the function.
        """
        results = [
            getattr(plugin, function_name)(**args)
            for plugin in self.plugins
            if hasattr(plugin, function_name)
        ]

        if not results:
            logger.error(f"Plugin with function '{function_name}' not found")
            return None

        return results
