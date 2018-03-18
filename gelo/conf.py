import configparser
import argparse


class Configuration(object):
    """A configuration for Gelo.
    I split this out to reduce coupling between Gelo and ConfigParser."""

    def __init__(self, config_file: configparser.ConfigParser,
                 args: argparse.Namespace):
        """Create a Configuration."""
        self.validate_config_file(config_file)
        self.user_plugin_dir = ""
        if 'user_plugin_dir' in config_file['core']:
            self.user_plugin_dir = config_file['core']['user_plugin_dir']
        if args.user_plugin_dir != '':
            self.user_plugin_dir = args.user_plugin_dir
        self.plugins = [plugin.split(':')[1] for plugin in config_file.keys()
                        if plugin.startswith('plugin:')]
        self.configparser = config_file
        self.show = args.show

    @staticmethod
    def validate_config_file(config_file: configparser.ConfigParser):
        """Check to see if the configuration file is valid.
        This is currently probably inadequate. It just looks for the [core]
        section."""
        errors = []
        if 'core' not in config_file:
            errors.append('Required config section [core] missing.')
        if len(errors) > 0:
            raise InvalidConfigurationError(errors)


class InvalidConfigurationError(Exception):
    """Used to indicate that the configuration is invalid."""


def is_int(value: str) -> bool:
    """Check to see if the value passed is an integer."""
    try:
        int(value)
    except ValueError:
        return False
    else:
        return True
