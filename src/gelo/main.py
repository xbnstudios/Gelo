# -*- coding: utf-8 -*-
"""A podcast chapter metadata gathering tool"""

import os
import logging
from time import time
from gelo import arch, mediator, shell
from gelo.plugins import (
    AudacityLabels,
    HttpPoller,
    HttpPusher,
    IRC,
    NowPlayingFile,
    OneEightyOneFM,
    SomaFM,
)


BUILTIN_PLUGIN_DIR = os.path.join(os.path.dirname(__file__), "plugins")


class GeloPluginManager:
    """Load Gelo plugins."""

    def __init__(self, config, mediator: arch.IMediator, show: str):
        """Create the PluginManager for Gelo."""
        self.config = config
        self.mediator = mediator
        self.show = show
        self.plugins = []
        self.pluginClasses = [
            AudacityLabels.AudacityLabels,
            HttpPoller.HttpPoller,
            HttpPusher.HttpPusher,
            IRC.IRC,
            NowPlayingFile.NowPlayingFile,
            OneEightyOneFM.OneEightyOneFM,
            SomaFM.SomaFM,
        ]

    def instantiatePlugin(self, element, element_name):
        """Instantiate a plugin."""
        c = self.config.configparser["plugin:" + element_name]
        return element(c, self.mediator, self.show)

    def getAllPlugins(self):
        """Get all of the plugins."""
        return self.plugins

    def getPluginByName(self, name, category="Default"):
        """Get the plugin object corresponding to a name and category."""
        for p in self.plugins:
            if p.PLUGIN_MODULE_NAME == name:
                return p
        return None

    def enablePluginByName(self, name, category="Default"):
        """Enable the named plugin in the given category.

        :param name: The name of the plugin to enable.
        :param category: The category that plugin is in.
        """
        to_enable = self.getPluginByName(name, category)
        if to_enable is not None:
            to_enable.enable()
            return to_enable
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

    def runAll(self):
        """Run all plugins.
        This constructs each plugin object and then calls its activate method.
        """
        for k in self.pluginClasses:
            name = k.__name__.removeprefix("gelo.plugins.")
            instance = self.instantiatePlugin(k, name)
            instance.activate()
            self.plugins.append(instance)

    def deactivateAll(self):
        """Deactivate all plugins."""
        for p in self.plugins:
            p.deactivate()

    def joinAll(self):
        """Join all plugin threads.
        This calls .join() on each plugin thread to ensure that they all exit at the end of the program.
        """
        for p in self.plugins:
            p.join()


class Gelo(object):
    def main(self, configuration):
        """Use the provided configuration to load all plugins and run Gelo."""
        logging.basicConfig(
            filename=configuration.log_file,
            format="%(asctime)s %(levelname)-8s %(name)s:%(message)s",
        )
        self.l = logging.getLogger("gelo")
        self.l.setLevel(configuration.log_level)
        self.l.info("Starting gelo at %s" % time())
        self.m = mediator.Mediator(configuration.broadcast_delay)
        self.gpm = GeloPluginManager(configuration, self.m, configuration.show)

        self.gpm.runAll()

        s = shell.GeloShell(self, self.gpm, self.m, configuration.macro_file)
        s.cmdloop()

        self.gpm.joinAll()

    def shutdown(self):
        self.l.info("Shutting down...")
        self.m.terminate()
        self.gpm.deactivateAll()
