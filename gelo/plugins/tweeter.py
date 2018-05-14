import gelo.arch
import gelo.conf
import gelo.mediator
import queue
import logging
import twitter
import twitter.error


class Tweeter(gelo.arch.IMarkerSink):
    """Tweet the tracks that you play."""

    PLUGIN_MODULE_NAME = 'tweeter'

    def __init__(self, config, mediator: gelo.arch.IMediator, show: str):
        """Create a new Tweeter."""
        super().__init__(config, mediator, show)
        self.log = logging.getLogger("gelo.plugins.Tweeter")
        self.validate_config()
        self.log.debug("Configuration valid")
        self.delayed = gelo.conf.as_bool(self.config['delayed'])
        self.channel = self.mediator.subscribe([gelo.arch.MarkerType.TRACK],
                                               Tweeter.__name__,
                                               delayed=self.delayed)
        self.api = self.get_api()

    def run(self):
        """Run the code that will receive markers and tweet them."""
        self.log.info("Starting plugin")
        while not self.should_terminate:
            try:
                marker = next(self.channel.listen())
                if not self.is_enabled:
                    continue
                self.log.debug("Received marker from channel: %s" % marker)
                self.tweet(marker)
            except queue.Empty:
                continue
            except gelo.mediator.UnsubscribeException:
                self.should_terminate = True

    def tweet(self, marker: gelo.arch.Marker):
        """Connect to Twitter and tweet the track."""
        special = " ({special})".format(special=marker.special) if \
            marker.special is not None else ""
        try:
            return self.api.PostUpdate(
                self.config['announce_string'].format(marker=marker.label,
                                                      special=special)
            )
        except twitter.error.TwitterError as e:
            if type(e.message) is list:
                if e.message[0]['code'] == 187:
                    self.log.warning("Twitter rejected duplicate status. "
                                     "Ignoring.")
            else:
                if e.message['code'] == 187:
                    self.log.warning("Twitter rejected duplicate status. "
                                     "Ignoring.")
                else:
                    raise e

    def get_api(self):
        """Get a Twitter API object from the python-twitter module."""
        return twitter.Api(
            consumer_key=self.config['consumer_key'],
            consumer_secret=self.config['consumer_secret'],
            access_token_key=self.config['access_token_key'],
            access_token_secret=self.config['access_token_secret']
        )

    def validate_config(self):
        """Ensure the configuration file is valid."""
        errors = []
        if 'consumer_key' not in self.config.keys():
            errors.append('[plugin:tweeter] is missing the required key'
                          ' "consumer_key"')
        if 'consumer_secret' not in self.config.keys():
            errors.append('[plugin:tweeter] is missing the required key'
                          ' "consumer_secret"')
        if 'access_token_key' not in self.config.keys():
            errors.append('[plugin:tweeter] is missing the required key'
                          ' "access_token_key"')
        if 'access_token_secret' not in self.config.keys():
            errors.append('[plugin:tweeter] is missing the required key'
                          ' "access_token_secret"')
        if 'announce_string' not in self.config.keys():
            errors.append('[plugin:tweeter] is missing the required key'
                          ' "announce_string"')
        if 'delayed' not in self.config.keys():
            self.config['delayed'] = 'True'
        else:
            if not gelo.conf.is_bool(self.config['delayed']):
                errors.append('[plugin:tweeter] has a non-boolean value for '
                              'the key "delayed"')
        if len(errors) > 0:
            raise gelo.conf.InvalidConfigurationError(errors)


def register():
    """Authorize this app to tweet from your account."""
    print('I haven\'t written this yet. Check back in v1.3.')
