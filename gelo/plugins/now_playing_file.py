import os
import queue
from gelo.configuration import InvalidConfigurationError
from gelo.architecture import IMarkerSink, IMediator, MarkerType


class NowPlayingFile(IMarkerSink):
    """Write the current TRACK marker to a text file."""

    def __init__(self, config, mediator: IMediator, show: str):
        """Create a new NowPlayingFile marker sink."""
        super().__init__(config, mediator, show)
        self.validate_config()
        self.channel = self.mediator.subscribe([MarkerType.TRACK])

    def run(self):
        """Run the marker-receiving code."""
        while not self.should_terminate:
            try:
                marker = next(self.channel.listen())
            except queue.Empty:
                continue
            with open(self.config['path'], "w") as f:
                f.write(marker.label)

    def validate_config(self):
        """Ensure the configuration is valid, and perform path expansion."""
        errors = []
        if 'path' not in self.config.keys():
            errors.append('[plugin:now_playing_file] is missing the required'
                          ' key "path"')
        else:
            self.config['path'] = os.path.expandvars(self.config['path'])
        # Return errors, if any
        if len(errors) > 0:
            raise InvalidConfigurationError(errors)
