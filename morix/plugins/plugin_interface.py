from abc import ABC, abstractmethod

class PluginInterface(ABC):
    @abstractmethod
    def initialize(self):
        """
        Initializes the plugin. This method must be implemented by all plugins.
        """
        pass