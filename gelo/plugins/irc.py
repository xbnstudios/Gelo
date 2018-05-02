import gelo
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
        self.server = self.config['server']
        self.port = self.config['port']
        self.tls = self.config['tls']
        self.send_to = self.config['send_to']
        self.message = self.config['message']

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
                c.privmsg(self.send_to, marker.label)
            except queue.Empty:
                continue
            except gelo.mediator.UnsubscribeException:
                self.should_terminate = True

    def validate_config(self):
        """Ensure the configuration file is valid."""
        errors = []
        if 'nick' not in self.config.keys():
            errors.append('[plugin:irc] is missing the required key "nick"')
        if 'server' not in self.config.keys():
            errors.append('[plugin:irc] is missing the required key "server"')
        if 'port' not in self.config.keys():
            errors.append('[plugin:irc] is missing the required key "port"')
        if 'tls' not in self.config.keys():
            errors.append('[plugin:irc] is missing the required key "tls"')
        if 'send_to' not in self.config.keys():
            errors.append('[plugin:irc] is missing the required key "send_to"')
        if 'message' not in self.config.keys():
            errors.append('[plugin:irc] is missing the required key "message"')
        if len(errors) > 0:
            raise gelo.conf.InvalidConfigurationError(errors)
