import os
import queue
import gelo


class AudacityLabels(gelo.arch.IMarkerSink):
    """Write every MarkerType.TRACK marker to a CSV file, but with tabs."""

    PLUGIN_MODULE_NAME = 'audacity_labels'
    LINE_TEMPLATE = "{start}\t{finish}\t{label}\n"

    def __init__(self, config, mediator: gelo.arch.IMediator, show: str):
        """Create a new NowPlayingFile marker sink."""
        super().__init__(config, mediator, show)
        self.validate_config()
        self.clear_file()
        self.channel = self.mediator.subscribe([ gelo.arch.MarkerType.TRACK])
        self.last_marker = None

    def run(self):
        """Run the marker-receiving code."""
        while not self.should_terminate:
            try:
                current_marker = next(self.channel.listen())
                if self.last_marker is not None:
                    line = self.create_line(current_marker)
                    with open(self.config['path'], 'a') as f:
                        f.write(line)
                    self.last_marker = current_marker
                else:
                    self.last_marker = current_marker
                    continue
            except queue.Empty:
                continue
            except gelo.mediator.UnsubscribeException:
                self.should_terminate = True
        if self.last_marker is not None:
            with open(self.config['path'], 'a') as f:
                f.write(self.LINE_TEMPLATE.format(
                    start=self.last_marker.time,
                    finish=self.last_marker.time,
                    label=self.last_marker.label
                ))

    def create_line(self, marker: gelo.arch.Marker) -> str:
        """Create a line for the file using the current marker and the last one.
        """
        return self.LINE_TEMPLATE.format(
            start=self.last_marker.time,
            finish=marker.time,
            label=self.last_marker.label
        )

    def clear_file(self):
        """Ensure the file is empty."""
        with open(self.config['path'], 'w') as f:
            f.write('')

    def validate_config(self):
        """Ensure the configuration is valid, and perform path expansion."""
        errors = []
        if 'path' not in self.config.keys():
            errors.append('[plugin:audacity_markers] is missing the required'
                          ' key "path"')
        else:
            self.config['path'] = os.path.expandvars(self.config['path'])
            self.config['path'] = self.config['path'].format(show=self.show)
        # Return errors, if any
        if len(errors) > 0:
            raise gelo.conf.InvalidConfigurationError(errors)
