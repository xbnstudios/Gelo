import gelo.main
import cmd
import readline
from yapsy import PluginManager


class GeloShell(cmd.Cmd):
    intro = "This is the Gelo control shell.  Type 'help' or '?' to list " \
            "commands.\n"
    prompt = "> "

    def __init__(self, g: gelo.main.Gelo, pm: PluginManager.PluginManager,
                 completekey='tab', stdin=None, stdout=None):
        """Create a new GeloShell.

        This method first calls the parent constructor, then saves the
        instances of Gelo and the Plugin Manager that were passed in.

        :param g: The running instance of Gelo to control.
        :param pm: The PluginManager in use by ``g``.
        """
        super(GeloShell, self).__init__(completekey=completekey, stdin=stdin,
                                        stdout=stdout)
        self.gelo = g
        self.plugin_manager = pm

    def emptyline(self):
        """When the user enters an empty line, do nothing."""
        pass

    def do_quit(self):
        """Exit the shell."""
        self.close()
        return True
