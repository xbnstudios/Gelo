import gelo.arch
import gelo.conf
import gelo.mediator
import sys
import queue
import irc.client


class IRC(gelo.arch.IMarkerSink):
    """Connect to IRC to send track names."""

    PLUGIN_MODULE_NAME = 'irc'

    def __init__(self, config, mediator: gelo.arch.IMediator, show: str):
        super().__init__(config, mediator, show)
        self.channel = self.mediator.subscribe([gelo.arch.MarkerType.TRACK])
        self.validate_config()
        self.nick = self.config['nick']
        if self.config['nickserv_pass'] != '':
            self.nickserv_enable = True
            self.nickserv_pass = self.config['nickserv_pass']
        else:
            self.nickserv_enable = False
        self.server = self.config['server']
        self.port = int(self.config['port'])
        self.tls = self.config['tls']
        self.send_to = self.config['send_to']
        self.message = self.config['message']

    def on_connect(self, connection, event):
        if self.nickserv_enable:
            connection.privmsg('nickserv', 'identify %s' % self.nickserv_pass)
        if irc.client.is_channel(self.send_to):
            connection.join(self.send_to)

    def on_disconnect(self, connection, event):
        self.should_terminate = True

    def on_join(self, connection, event):
        pass

    def run(self):
        """Run the code that will receive markers and post them to IRC."""
        reactor = irc.client.Reactor()
        try:
            c = reactor.server().connect(self.server, self.port, self.nick)
        except irc.client.ServerConnectionError:
            print(sys.exc_info()[1])
            raise SystemExit(1)
        c.add_global_handler("welcome", self.on_connect)
        c.add_global_handler("disconnect", self.on_disconnect)
        c.add_global_handler("join", self.on_join)
        while not self.should_terminate:
            try:
                reactor.process_once(timeout=0.5)
                # TODO: this should timeout too
                marker = next(self.channel.listen())
                c.privmsg(self.send_to, self.make_message(marker))
            except queue.Empty:
                continue
            except gelo.mediator.UnsubscribeException:
                self.should_terminate = True

    def make_message(self, marker: gelo.arch.Marker):
        """Make the text of the message to send."""
        return self.message.format(marker=marker.label)

    def validate_config(self):
        """Ensure the configuration file is valid."""
        errors = []
        if 'nick' not in self.config.keys():
            errors.append('[plugin:irc] is missing the required key "nick"')
        if 'nickserv_pass' not in self.config.keys():
            errors.append('[plugin:irc] is missing the required key '
                          '"nickserv_pass"')
        if 'server' not in self.config.keys():
            errors.append('[plugin:irc] is missing the required key "server"')
        if 'port' not in self.config.keys():
            errors.append('[plugin:irc] is missing the required key "port"')
        else:
            if not gelo.conf.is_int(self.config['port']):
                errors.append('[plugin:irc] has a non-numeric value for'
                              'the key "port"')
            else:
                if int(self.config['port']) >= 65536:
                    errors.append('[plugin:irc] has a value greater than'
                                  ' 65535 for the key "port", which is not'
                                  ' supported by TCP')
        if 'tls' not in self.config.keys():
            errors.append('[plugin:irc] is missing the required key "tls"')
        if 'send_to' not in self.config.keys():
            errors.append('[plugin:irc] is missing the required key "send_to"')
        if 'message' not in self.config.keys():
            errors.append('[plugin:irc] is missing the required key "message"')
        if len(errors) > 0:
            raise gelo.conf.InvalidConfigurationError(errors)
