import queue
import twitter
from gelo.configuration import InvalidConfigurationError
from gelo.architecture import IMarkerSink, IMediator, MarkerType


class Tweeter(IMarkerSink):
    """Tweet the tracks that you play."""
    def __init__(self, config, mediator: IMediator, show: str):
        """Create a new Tweeter."""
        super().__init__(config, mediator, show)
        self.validate_config()
        self.channel = self.mediator.subscribe([MarkerType.TRACK])
        self.api = self.get_api()

    def run(self):
        """Run the code that will receive markers and tweet them."""
        while not self.should_terminate:
            try:
                marker = next(self.channel.listen())
            except queue.Empty:
                continue
            self.tweet(marker.label)

    def tweet(self, marker: str):
        """Connect to Twitter and tweet the track."""
        return self.api.PostUpdate(
            self.config['announce_string'].format(marker=marker)
        )

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
        if len(errors) > 0:
            raise InvalidConfigurationError(errors)


def register():
    """Authorize this app to tweet from your account."""
    print('I haven\'t written this yet. Check back in v1.1.')
