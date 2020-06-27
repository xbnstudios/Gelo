import gelo.arch
import gelo.conf
import gelo.mediator
import sys
import ssl
import queue
import logging
import irc.client


class IRC(gelo.arch.IMarkerSink):
    """Connect to IRC to send track names."""

    PLUGIN_MODULE_NAME = "IRC"

    def __init__(self, config, mediator: gelo.arch.IMediator, show: str):
        super().__init__(config, mediator, show)
        self.log = logging.getLogger("gelo.plugins.irc")
        self.validate_config()
        self.log.debug("Configuration validated")
        self.nick = self.config["nick"]
        if "nickserv_pass" in self.config:
            self.log.debug("Enabling NickServ authentication")
            self.nickserv_enable = True
            self.nickserv_pass = self.config["nickserv_pass"]
        else:
            self.log.debug("Disabling NickServ authentication")
            self.nickserv_enable = False
        self.server = self.config["server"]
        self.port = self.config["port"]
        self.tls = self.config["tls"]
        self.ipv6 = self.config["ipv6"]
        self.send_to = self.config["send_to"]
        if "repeat_with" in self.config:
            self.repeat_with = self.config["repeat_with"]
        else:
            self.repeat_with = None
        self.message = self.config["message"]
        self.delayed = self.config["delayed"]
        self.channel = self.mediator.subscribe(
            [gelo.arch.MarkerType.TRACK], IRC.__name__, delayed=self.delayed
        )
        self.ready = False

    def on_connect(self, connection, event):
        self.log.debug("Finished connecting to IRC")
        if self.nickserv_enable:
            connection.privmsg("nickserv", "identify %s" % self.nickserv_pass)
            self.log.debug("Sent NickServ auth message")
        if irc.client.is_channel(self.send_to):
            self.log.debug("Joining output channel")
            connection.join(self.send_to)
        else:
            self.ready = True

    def on_disconnect(self, connection, event):
        self.log.info("IRC server disconnected.")
        self.should_terminate = True

    def on_join(self, connection, event):
        self.log.debug("Joined output channel")
        self.ready = True

    def run(self):
        """Run the code that will receive markers and post them to IRC."""
        self.log.debug("Plugin started")
        reactor = irc.client.Reactor()
        try:
            wrapper = ssl.wrap_socket if self.tls else irc.client.connection.identity
            factory = irc.client.connection.Factory(ipv6=self.ipv6, wrapper=wrapper)
            self.log.debug(
                "Attempting to connect to %s:%s with nick %s"
                % (self.server, self.port, self.nick)
            )
            c = reactor.server().connect(
                self.server, self.port, self.nick, connect_factory=factory
            )
            self.log.debug("Connected!")
            c.add_global_handler("welcome", self.on_connect)
            c.add_global_handler("disconnect", self.on_disconnect)
            c.add_global_handler("join", self.on_join)

            while not self.should_terminate:
                reactor.process_once(timeout=0.2)
                self.main_once(c)
        except irc.client.ServerConnectionError:
            self.log.critical("IRC connection error: " + str(sys.exc_info()[1]))

    def main_once(self, connection: irc.client.connection, timeout=0.2):
        """Fetch new markers from the queue and send them in IRC.

        :param connection: The connection to the IRC server to send messages
        via.
        :param timeout: The length of time (in seconds, float) to wait before
        continuing.
        """
        if not self.ready:
            return
        try:
            marker = next(self.channel.listen(timeout=timeout))
            if not self.is_enabled:
                return
            self.log.debug("Received marker from channel: %s" % marker)
            self.send_message(marker, connection)
        except StopIteration:
            return
        except queue.Empty:
            self.log.debug("Queue empty, continuing...")
        except gelo.mediator.UnsubscribeException:
            self.log.info("Queue closed, exiting...")
            self.should_terminate = True
            connection.quit(message="Metadata system shutdown")

    def send_message(self, marker: gelo.arch.Marker, c: irc.client.connection):
        """Use the provided connection to send a message (or several,
        if configured) about the provided marker.
        :param marker: The marker to message about.
        :param c: The connection to send messages on.
        """
        # Build the "special" string. " (Bit Perfectly)" if set, otherwise ""
        special = (
            " ({special})".format(special=marker.special)
            if marker.special is not None
            else ""
        )
        if self.repeat_with is not None:
            # Send message with each of the repeat items
            for item in self.repeat_with:
                to_send = self.message.format(
                    marker=marker.label.strip("\n"), special=special, item=item
                )
                self.log.debug("Sending message: %s" % to_send)
                c.privmsg(self.send_to, to_send)
        else:
            # Send just one message
            to_send = self.message.format(
                marker=marker.label.strip("\n"), special=special
            )
            self.log.debug("Sending message: %s" % to_send)
            c.privmsg(self.send_to, to_send)

    def validate_config(self):
        """Ensure the configuration file is valid."""
        errors = []
        if "nick" not in self.config.keys():
            errors.append('[plugin:irc] is missing the required key "nick"')
        if "server" not in self.config.keys():
            errors.append('[plugin:irc] is missing the required key "server"')
        if "port" not in self.config.keys():
            errors.append('[plugin:irc] is missing the required key "port"')
        else:
            if type(self.config["port"]) is not int:
                errors.append('[plugin:irc] has a non-numeric value for the key "port"')
            else:
                if self.config["port"] >= 65536:
                    errors.append(
                        '[plugin:irc] has a value greater than 65535 for the key "port"'
                        ", which is not supported by TCP"
                    )
        if "tls" not in self.config.keys():
            errors.append('[plugin:irc] is missing the required key "tls"')
        else:
            if type(self.config["tls"]) is not bool:
                errors.append(
                    "[plugin:irc] must have a boolean value for the " 'key "tls"'
                )
        if "ipv6" not in self.config.keys():
            errors.append('[plugin:irc] is missing the required key "ipv6"')
        else:
            if type(self.config["ipv6"]) is not bool:
                errors.append(
                    "[plugin:irc] must have a boolean value for the " 'key "tls"'
                )
        if "send_to" not in self.config.keys():
            errors.append('[plugin:irc] is missing the required key "send_to"')
        if "message" not in self.config.keys():
            errors.append('[plugin:irc] is missing the required key "message"')
        if "delayed" not in self.config.keys():
            self.config["delayed"] = "True"
        if "repeat_with" in self.config.keys():
            if type(self.config["repeat_with"]) is not list:
                errors.append(
                    '[plugin:IRC] must have an array for the key "repeat_with"'
                )
            else:
                for repeat_item in self.config["repeat_with"]:
                    if type(repeat_item) is not str:
                        errors.append(
                            "[plugin:IRC] must have string values for "
                            "every element of the array at the key "
                            '"repeat_with". Ensure every element has quotes.'
                        )
                        break
        else:
            if type(self.config["delayed"]) is not bool:
                errors.append(
                    '[plugin:irc] has a non-boolean value for the key "delayed"'
                )
        if len(errors) > 0:
            raise gelo.conf.InvalidConfigurationError(errors)
