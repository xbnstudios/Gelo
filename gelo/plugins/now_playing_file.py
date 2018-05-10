import os
from gelo import arch, conf, mediator
import queue


class NowPlayingFile(arch.IMarkerSink):
    """Write the current TRACK marker to a text file."""

    PLUGIN_MODULE_NAME = 'now_playing_file'

    def __init__(self, config, med: arch.IMediator, show: str):
        """Create a new NowPlayingFile marker sink."""
        super().__init__(config, med, show)
        self.validate_config()
        self.channel = self.mediator.subscribe([arch.MarkerType.TRACK],
                                               NowPlayingFile.__name__)

    def run(self):
        """Run the marker-receiving code."""
        while not self.should_terminate:
            try:
                marker = next(self.channel.listen())
                if not self.is_enabled:
                    continue
                with open(self.config['path'], "w") as f:
                    f.write(marker.label)
            except queue.Empty:
                continue
            except mediator.UnsubscribeException:
                self.should_terminate = True

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
            raise conf.InvalidConfigurationError(errors)
