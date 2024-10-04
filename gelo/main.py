# -*- coding: utf-8 -*-
"""A podcast chapter metadata gathering tool"""

import os
import logging
from time import time
from gelo import arch, mediator, shell
from yapsy import PluginManager, PluginFileLocator


BUILTIN_PLUGIN_DIR = os.path.join(os.path.dirname(__file__), "plugins")


class GeloPluginManager(PluginManager.PluginManager):
    """Load Gelo plugins (just override the method that instantiates plugins)."""

    def __init__(self, plugin_locator=None):
        """Create the PluginManager for Gelo."""
        if plugin_locator is None:
            plugin_locator = PluginFileLocator.PluginFileAnalyzerWithInfoFile(
                "GeloPluginAnalyzer", extensions="gelo-plugin"
            )
        super().__init__(
            categories_filter=None, directories_list=None, plugin_locator=plugin_locator
        )
        self.config = None
        self.mediator = None
        self.show = None

    def set_cms(self, config, mediator: arch.IMediator, show: str) -> None:
        """Set the config, mediator, and show to load plugins with."""
        self.config = config
        self.mediator = mediator
        self.show = show

    def instanciateElementWithImportInfo(
        self, element, element_name, plugin_module_name, candidate_filepath
    ):
        """Instantiate a plugin.
        The typo is intentional, because that's how the framework spells it."""
        c = self.config.configparser["plugin:" + element_name]
        return element(c, self.mediator, self.show)

    def instanciateElement(self, element):
        """Instantiate a plugin.
        This function is backwards and stupid. It is deprecated in a
        yet-to-be released version of Yapsy. When that version is released,
        this class will automatically upgrade to the not-stupid version."""
        return element(self.config.configparser, self.mediator, self.show)

    def enablePluginByName(self, name, category="Default"):
        """Enable the named plugin in the given category.

        :param name: The name of the plugin to enable.
        :param category: The category that plugin is in.
        """
        to_enable = self.getPluginByName(name, category)
        if to_enable is not None:
            eo = to_enable.plugin_object
            if eo is not None:
                eo.enable()
                return eo
        return None

    def disablePluginByName(self, name, category="Default"):
        """Disable the named plugin in the given category.

        :param name: The name of the plugin to disable.
        :param category: The category that plugin is in.
        """
        to_disable = self.getPluginByName(name, category)
        if to_disable is not None:
            do = to_disable.plugin_object
            if do is not None:
                do.disable()
                return do
        return None


class Gelo(object):
    def main(self, configuration):
        """Use the provided configuration to load all plugins and run Gelo."""
        logging.basicConfig(
            filename=configuration.log_file,
            format="%(asctime)s %(levelname)-8s %(name)s:%(" "message)s",
        )
        self.l = logging.getLogger("gelo")
        self.l.setLevel(configuration.log_level)
        self.l.info("Starting gelo at %s" % time())
        pfa = PluginFileLocator.PluginFileAnalyzerWithInfoFile(
            "gelo_info_ext", extensions="gelo-plugin"
        )
        pfl = PluginFileLocator.PluginFileLocator()
        pfl.removeAnalyzers("info_ext")
        pfl.appendAnalyzer(pfa)
        pfl.setPluginPlaces([BUILTIN_PLUGIN_DIR, configuration.user_plugin_dir])
        self.l.info(
            "Plugin locations: %s"
            % ([BUILTIN_PLUGIN_DIR, configuration.user_plugin_dir])
        )
        self.gpm = GeloPluginManager(plugin_locator=pfl)
        self.m = mediator.Mediator(configuration.broadcast_delay)
        self.gpm.set_cms(configuration, self.m, configuration.show)
        self.l.info("Collecting plugins...")
        self.gpm.collectPlugins()

        for plugin in self.gpm.getAllPlugins():
            self.l.info("Starting %s..." % plugin.plugin_object.PLUGIN_MODULE_NAME)
            plugin.plugin_object.activate()

        s = shell.GeloShell(self, self.gpm, self.m, configuration.macro_file)
        s.cmdloop()

        for plugin in self.gpm.getAllPlugins():
            plugin.plugin_object.join()

    def shutdown(self):
        self.l.info("Shutting down...")
        self.m.terminate()
        for plugin in self.gpm.getAllPlugins():
            self.l.info(
                "Telling %s to exit..." % plugin.plugin_object.PLUGIN_MODULE_NAME
            )
            plugin.plugin_object.deactivate()
