# -*- coding: utf-8 -*-
"""Gelo: a podcast chapter metadata gathering tool"""
from .mediator import Mediator
from .arch import IMediator
from yapsy.PluginManager import PluginManager
from yapsy.PluginFileLocator import PluginFileLocator

BUILTIN_PLUGIN_DIR = './plugins'


class GeloPluginManager(PluginManager):
    """Load Gelo plugins (just override the method that instantiates plugins).
    """
    def __init__(self, plugin_locator=None):
        """Create the PluginManager for Gelo."""
        super().__init__(categories_filter=None,
                         directories_list=None,
                         plugin_locator=plugin_locator)
        self.config = None
        self.mediator = None
        self.show = None

    def set_cms(self, config, mediator: IMediator, show: str) -> None:
        """Set the config, mediator, and show to load plugins with."""
        self.config = config
        self.mediator = mediator
        self.show = show

    def instanciateElementWithImportInfo(self, element, element_name,
                                         plugin_module_name,
                                         candidate_filepath):
        """Instantiate a plugin.
        The typo is intentional, because that's how the framework spells it."""
        c = self.config.configparser['plugin:' + plugin_module_name]
        return element(c, self.mediator, self.show)

    def instanciateElement(self, element):
        """Instantiate a plugin.
        This function is backwards and stupid. It is deprecated in a
        yet-to-be released version of Yapsy. When that version is released,
        this class will automatically upgrade to the not-stupid version."""
        return element(self.config.configparser, self.mediator, self.show)


class Gelo(object):
    def main(self, configuration):
        """Use the provided configuration to load all plugins and run Gelo."""
        pfl = PluginFileLocator()
        pfl.setPluginPlaces(
            [BUILTIN_PLUGIN_DIR, configuration.user_plugin_dir]
        )
        self.gpm = GeloPluginManager(plugin_locator=pfl)
        m = Mediator()
        self.gpm.set_cms(configuration, m, configuration.show)
        self.gpm.collectPlugins()

        for plugin in self.gpm.getAllPlugins():
            plugin.plugin_object.start()
        for plugin in self.gpm.getAllPlugins():
            plugin.plugin_object.join()

    def shutdown(self):
        for plugin in self.gpm.getAllPlugins():
            plugin.exit()
