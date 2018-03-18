# -*- coding: utf-8 -*-
"""Gelo: a podcast chapter metadata gathering tool"""
from .architecture import IMediator
from .mediator import Mediator
from yapsy.PluginManager import PluginManager
from yapsy.PluginFileLocator import PluginFileLocator

BUILTIN_PLUGIN_DIR = './gelo/plugins'


class GeloPluginManager(PluginManager):
    """Load Gelo plugins (just override the method that instantiates plugins).
    """
    def __init__(self, plugin_locator=None):
        """Create the PluginManager for Gelo."""
        super().__init__(categories_filter=None,
                         directories_list=None,
                         plugin_info_ext="gelo-plugin",
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
        c = self.config['plugin:' + plugin_module_name]
        return element(c, self.mediator, self.show)


class Gelo(object):
    def main(self, configuration):
        """Use the provided configuration to load all plugins and run Gelo."""
        pfl = PluginFileLocator()
        pfl.setPluginPlaces(
            [BUILTIN_PLUGIN_DIR, configuration.user_plugin_dir]
        )
        self.gpm = GeloPluginManager(plugin_locator=pfl)
        m = Mediator()
        self.gpm.set_cms(configuration.configparser, m, configuration.show)
        self.gpm.locatePlugins()
        self.gpm.loadPlugins()

        for plugin in self.gpm.getAllPlugins():
            plugin.start()

    def shutdown(self):
        for plugin in self.gpm.getAllPlugins():
            plugin.exit()
