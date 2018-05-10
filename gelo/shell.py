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
        return "\n".join(self.commands) + "\n"

    @staticmethod
    def deserialize(serialized: str):
        """Turn a string from serialize back into a macro."""
        m = Macro()
        m.commands = serialized.split("\n")[:-1]
        return m


class GeloMacroShell(cmd.Cmd):
    intro = "Submit a blank line to end the macro."
    prompt = "macro> "

    def __init__(self, m: Macro, completekey='tab', stdin=None, stdout=None):
        """Create a new GeloMacroShell.

        Like a GeloShell, but doesn't execute any of the commands, only saves
        them in the Macro passed in as an argument.  It does validate them
        for correctness, to help avoid spelling errors and such.
        :param m: The macro to save commands in.
        """
        super(GeloMacroShell, self).__init__(completekey=completekey,
                                             stdin=stdin, stdout=stdout)
        self.macro = m

    def emptyline(self):
        """When the user enters an empty line, quit."""
        return True

    def do_squelch(self, arg):
        """Ignore the next marker from any source plugin.

        Usage: `squelch`"""
        pass

    def do_stop(self, arg):
        """Ignore all markers from every source plugin until start is issued.

        Usage: `stop`"""
        pass

    def do_start(self, arg):
        """Pass markers from any source plugin.

        This is the default, and this command need not be issued when the
        shell opens.

        Usage: `start`"""
        pass

    def do_load(self, arg):
        """Load the named plugin.

        An error message is printed when the plugin does not exist, and the
        command is silently ignored if the plugin is already loaded.

        Usage: `load http_poller`"""
        pass

    def do_unload(self, arg):
        """Unload the named plugin.

        An error message is printed when the plugin does not exist, and the
        command is silently ignored if the plugin is already unloaded.

        Usage: `unload http_poller`"""
        pass


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
        tmp = configparser.ConfigParser()
        self.macro_file = macro_file
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
        m = Macro()
        s = GeloMacroShell(m)
        s.cmdloop()
        # Save the macro, somehow

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

    def do_undefine(self, arg):
        """Undefine the named macro.

        Remove the saved definition for the named macro. Undefining a macro
        that is not defined will result in an error message.

        Usage: `undefine a_macro`"""
        pass

    def default(self, line):
        """Try running a macro, or display an error message."""
        print("gelo: unrecognized command")

    def do_quit(self, arg):
        """Terminate all plugins and exit Gelo.

        Usage: `quit`"""
        self.gelo.shutdown()
        return True
