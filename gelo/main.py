# -*- coding: utf-8 -*-
"""Gelo: a podcast chapter metadata gathering tool"""
import os
import grp
import pwd
# import pydevd
from gelo import arch, mediator
from yapsy import PluginManager, PluginFileLocator

# pydevd.settrace(
#     'localhost',
#     port=9999,
#     stdoutToServer=True,
#     stderrToServer=True)
BUILTIN_PLUGIN_DIR = os.path.join(os.path.dirname(__file__), 'plugins')


class GeloPluginManager(PluginManager.PluginManager):
    """Load Gelo plugins (just override the method that instantiates plugins).
    """

    def __init__(self, plugin_locator=None):
        """Create the PluginManager for Gelo."""
        if plugin_locator is None:
            plugin_locator = PluginFileLocator.PluginFileAnalyzerWithInfoFile(
                'GeloPluginAnalyzer',
                extensions='gelo-plugin'
            )
        super().__init__(categories_filter=None,
                         directories_list=None,
                         plugin_locator=plugin_locator)
        self.config = None
        self.mediator = None
        self.show = None

    def set_cms(self, config, mediator: arch.IMediator, show: str) \
            -> None:
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
        pfa = PluginFileLocator.PluginFileAnalyzerWithInfoFile(
            'gelo_info_ext',
            extensions='gelo-plugin'
        )
        pfl = PluginFileLocator.PluginFileLocator()
        pfl.removeAnalyzers('info_ext')
        pfl.appendAnalyzer(pfa)
        pfl.setPluginPlaces(
            [BUILTIN_PLUGIN_DIR, configuration.user_plugin_dir]
        )
        self.gpm = GeloPluginManager(plugin_locator=pfl)
        self.m = mediator.Mediator()
        self.gpm.set_cms(configuration, self.m, configuration.show)
        self.gpm.collectPlugins()

        for plugin in self.gpm.getAllPlugins():
            plugin.plugin_object.start()
        self.drop_privileges(
            user=configuration.configparser['core'].get('unprivileged_user',
                                                        'nobody'),
            group=configuration.configparser['core'].get('unprivileged_group',
                                                         'nogroup')
        )
        for plugin in self.gpm.getAllPlugins():
            plugin.plugin_object.join()

    def shutdown(self):
        self.m.terminate()
        for plugin in self.gpm.getAllPlugins():
            plugin.plugin_object.exit()

    def drop_privileges(self, user='nobody', group='nogroup'):
        """Drop privileges to the specified user and group.
        By default, this function de-elevates to nobody/nogroup.
        :param user: The user to drop privileges to
        :param group: The group to drop privileges to"""
        if os.getuid() != 0:
            # I'm not root, nothing to do.
            return
        unpriv_uid = pwd.getpwnam(user)[2]
        unpriv_gid = grp.getgrnam(group)[2]
        try:
            os.setgid(unpriv_gid)
        except OSError as ose:
            print("Could not drop privileges to", group)
            print(ose.strerror)
        try:
            os.setuid(unpriv_uid)
        except OSError as ose:
            print("Could not drop privileges to", user)
            print(ose.strerror)
        os.umask(0o77)
        print('successfully dropped privileges')
