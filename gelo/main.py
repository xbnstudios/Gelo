# -*- coding: utf-8 -*-
"""Gelo: a podcast chapter metadata gathering tool"""
from yapsy.PluginManager import PluginManager

BUILTIN_PLUGIN_DIR = './gelo/plugins'

def main(configuration):
    """Use the provided configuration to load all plugins and run Gelo."""

    pm = PluginManager()
    pm.setPluginPlaces([BUILTIN_PLUGIN_DIR, configuration.user_plugin_dir])

    print("Plugins with configurations:", configuration.plugins)
