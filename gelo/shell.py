import cmd
from gelo import mediator, arch, main
import configparser
import logging
import readline
from yapsy import PluginManager


class Macro(object):
    """A set of commands."""
    def __init__(self):
        self.commands = []

    def append(self, cmd: str):
        """Append a command to this macro."""
        self.commands.append(cmd)

    def serialize(self) -> str:
        """Serialize this macro into a string, for the config file."""
        return "\n".join(self.commands)

    @staticmethod
    def deserialize(serialized: str):
        """Turn a string from serialize back into a macro."""
        m = Macro()
        m.commands = serialized.split("\n")
        return m


class GeloMacroShell(cmd.Cmd):
    intro = "Type `end` to finish the macro."
    prompt = "macro> "

    def __init__(self, m: Macro, pm, completekey='tab', stdin=None,
                 stdout=None):
        """Create a new GeloMacroShell.

        Like a GeloShell, but doesn't execute any of the commands, only saves
        them in the Macro passed in as an argument.  It does validate them
        for correctness, to help avoid spelling errors and such.
        :param m: The macro to save commands in.
        :param pm: The PluginManager the system is currently using.
        """
        super(GeloMacroShell, self).__init__(completekey=completekey,
                                             stdin=stdin, stdout=stdout)
        self.macro = m
        self.plugin_manager = pm

    def emptyline(self):
        """When the user enters an empty line, do nothing."""
        pass

    def do_squelch(self, arg):
        """Ignore the next marker from any source plugin.

        Usage: `squelch`"""
        self.macro.append("squelch")

    def do_stop(self, arg):
        """Ignore all markers from every source plugin until start is issued.

        Usage: `stop`"""
        self.macro.append("stop")

    def do_start(self, arg):
        """Pass markers from any source plugin.

        This is the default, and this command need not be issued when the
        shell opens.

        Usage: `start`
        """
        self.macro.append("start")

    def do_enable(self, arg):
        """Enable the named plugin.

        An error message is printed when the plugin does not exist, and the
        command is silently ignored if the plugin is already enabled.

        Usage: `enable HttpPoller`"""
        if ' ' in arg:
            print("gelo: macro: load: invalid command format")
            return False
        plugin = self.plugin_manager.getPluginByName(arg)
        if plugin is None:
            print("gelo: macro: load: nonexistent plugin \"%s\"" % arg)
            return False
        self.macro.append("enable " + arg)

    def do_disable(self, arg):
        """Disable the named plugin.

        An error message is printed when the plugin does not exist, and the
        command is silently ignored if the plugin is already disabled.

        Usage: `disable HttpPoller`"""
        if ' ' in arg:
            print("gelo: macro: unload: invalid command format")
            return False
        plugin = self.plugin_manager.getPluginByName(arg)
        if plugin is None:
            print("gelo: macro: unload: nonexistent plugin \"%s\"" % arg)
            return False
        self.macro.append("disable " + arg)

    def do_inject(self, arg):
        """Inject a marker into the system, as if from a source plugin.

        The first word after the command must be either TRACK or TOPIC.
        Everything after that is considered the marker text, and will be sent
        along to the sink plugins. To save your pinkies, the marker type will be
        automatically uppercased for you.

        Usage: `inject TRACK Justice - Fire`
        """
        if ' ' not in arg:
            print("gelo: inject: invalid command format")
            return False
        split_point = arg.find(' ')
        marker_type = arg[:split_point].upper()
        marker_type = arch.MarkerType.from_string(marker_type)
        if marker_type is None:
            print("gelo: inject: invalid marker type")
            return False
        self.macro.append("inject " + arg)

    def do_end(self, arg):
        """Finish adding to the macro.

        Usage: `end`
        """
        return True


class GeloShell(cmd.Cmd):
    intro = "This is the Gelo control shell.  Type 'help' or '?' to list " \
            "commands.\n"
    prompt = "> "

    def __init__(self, g, pm, m: mediator.Mediator,
                 macro_file, completekey='tab', stdin=None, stdout=None):
        """Create a new GeloShell.

        This method first calls the parent constructor, then saves the
        instances of Gelo and the Plugin Manager that were passed in.

        :param g: The running instance of Gelo to control. Not type hinted
        because Python weirdness?
        :param pm: The GeloPluginManager in use by ``g``. Also not type hinted
        :param m: The Mediator that's currently passing Messages.
        because Python weirdness?
        :param macro_file: The path to the file in which macros are saved.
        """
        super(GeloShell, self).__init__(completekey=completekey, stdin=stdin,
                                        stdout=stdout)
        self.gelo = g
        self.mediator = m
        self.plugin_manager = pm
        self.macro_file = macro_file
        self.macros = configparser.ConfigParser()
        self.macros.read(macro_file)
        if 'macros' not in self.macros.keys():
            self.macros['macros'] = {}
        self.log = logging.getLogger(__name__)

    def emptyline(self):
        """When the user enters an empty line, do nothing."""
        pass

    def do_squelch(self, arg):
        """Ignore the next marker from any source plugin.

        Usage: `squelch`"""
        self.mediator.shouldSquelchNext = True

    def do_stop(self, arg):
        """Ignore all markers from every source plugin until start is issued.

        Usage: `stop`"""
        self.mediator.stopped = True

    def do_start(self, arg):
        """Pass markers from any source plugin.

        This is the default, and this command need not be issued when the
        shell opens.

        Usage: `start`"""
        self.mediator.stopped = False

    def do_enable(self, arg):
        """Enable the named plugin.

        An error message is printed when the plugin does not exist, and the
        command is silently ignored if the plugin is already enabled.

        Usage: `enable HttpPoller`"""
        if ' ' in arg:
            print("gelo: load: invalid command format")
            return False
        plugin = self.plugin_manager.getPluginByName(arg)
        if plugin is None:
            print("gelo: load: nonexistent plugin \"%s\"" % arg)
            return False
        if plugin.plugin_object.is_enabled:
            return False
        self.plugin_manager.enablePluginByName(arg)
        self.log.info("Plugin enabled: %s" % arg)

    def do_disable(self, arg):
        """Disable the named plugin.

        An error message is printed when the plugin does not exist, and the
        command is silently ignored if the plugin is already disabled.

        Usage: `disable HttpPoller`"""
        if ' ' in arg:
            print("gelo: unload: invalid command format")
            return False
        plugin = self.plugin_manager.getPluginByName(arg)
        if plugin is None:
            print("gelo: unload: nonexistent plugin \"%s\"" % arg)
            return False
        if not plugin.plugin_object.is_enabled:
            return False
        self.plugin_manager.disablePluginByName(arg)
        self.log.info("Plugin disabled: %s" % arg)

    def do_define(self, arg):
        """Define a macro, with the given name.

        Issuing this command changes the prompt to a special macro-recording
        mode. In this mode, all commands entered will be saved as a
        replayable macro. To exit this mode, enter just a blank line.

        Macro names may not have spaces, although other characters are
        permitted. Using characters outside of the US-ASCII character set
        should work fine, but I make no promises.

        To run a macro, type its name at the command prompt.

        Usage: `define a_macro`"""
        if ' ' in arg:
            print('gelo: define: spaces not permitted in macro name')
            return False
        m = Macro()
        s = GeloMacroShell(m, self.plugin_manager)
        s.cmdloop()
        self.macros['macros'][arg] = m.serialize()

    def do_undefine(self, arg):
        """Undefine the named macro.

        Remove the saved definition for the named macro. Undefining a macro
        that is not defined will result in an error message.

        Usage: `undefine a_macro`
        """
        if ' ' in arg:
            print('gelo: undefine: spaces not permitted in macro name')
            return False
        del(self.macros['macros'][arg])

    def do_list(self, arg):
        """List all of the macros and plugins currently known.

        Optionally, specify one of "macros" or "plugins" to list just those.

        Usage: `list macros`
        """
        if arg not in ['macros', 'plugins', '']:
            print("gelo: list: invalid argument")
            return False
        if arg == "macros" or arg == "":
            print("Macros:")
            if len(self.macros['macros'].keys()) == 0:
                print("\t(no macros defined)")
            for key in self.macros['macros'].keys():
                print("\t" + key)
        if arg == "plugins" or arg == "":
            print("Plugins:")
            for plugin in self.plugin_manager.getAllPlugins():
                print("\t" + plugin.name)

    def do_inject(self, arg):
        """Inject a marker into the system, as if from a source plugin.

        The first word after the command must be either TRACK or TOPIC.
        Everything after that is considered the marker text, and will be sent
        along to the sink plugins. To save your pinkies, the marker type will be
        automatically uppercased for you.

        Usage: `inject TRACK Justice - Fire`
        """
        # parse arg
        if ' ' not in arg:
            print("gelo: inject: invalid command format")
            return False
        split_point = arg.find(' ')
        marker_type = arg[:split_point].upper()
        marker = arg[split_point+1:]
        marker_type = arch.MarkerType.from_string(marker_type)
        if marker_type is None:
            print("gelo: inject: invalid marker type")
            return False
        # create marker
        m = arch.Marker(marker)
        # inject marker
        self.mediator.publish(marker_type, m)

    def default(self, line):
        """Try running a macro, or display an error message."""
        line = line.strip()
        if line in self.macros['macros'].keys():
            self.cmdqueue.extend(self.macros['macros'][line].split("\n"))
        else:
            print("gelo: unrecognized command")

    def do_quit(self, arg):
        """Terminate all plugins, save macro changes, and exit Gelo.

        Usage: `quit`"""
        self.gelo.shutdown()
        with open(self.macro_file, 'w') as fp:
            self.macros.write(fp)
        return True
