import os
from gelo import arch, conf, mediator
import queue


class NowPlayingFile(arch.IMarkerSink):
    """Write the current TRACK marker to a text file."""

    PLUGIN_MODULE_NAME = "NowPlayingFile"

    def __init__(self, config, med: arch.IMediator, show: str):
        """Create a new NowPlayingFile marker sink."""
        super().__init__(config, med, show)
        self.validate_config()
        self.delayed = self.config["delayed"]
        self.channel = self.mediator.subscribe(
            [arch.MarkerType.TRACK], NowPlayingFile.__name__, delayed=self.delayed
        )

    def run(self):
        """Run the marker-receiving code."""
        while not self.should_terminate:
            try:
                marker = next(self.channel.listen())
                if not self.is_enabled:
                    continue
                with open(self.config["path"], "wb") as f:
                    # B.U.T.T. doesn't Do the Right Thing™ when encountering
                    # Unicode characters.
                    text = marker.label.replace("—", "-")
                    f.write(text.encode("latin-1", "ignore"))
            except queue.Empty:
                continue
            except mediator.UnsubscribeException:
                self.should_terminate = True

    def validate_config(self):
        """Ensure the configuration is valid, and perform path expansion."""
        errors = []
        if "path" not in self.config.keys():
            errors.append(
                '[plugin:now_playing_file] is missing the required key "path"'
            )
        else:
            self.config["path"] = os.path.expandvars(self.config["path"])
        if "delayed" not in self.config.keys():
            self.config["delayed"] = "False"
        else:
            if type(self.config["delayed"]) is not bool:
                errors.append(
                    "[plugin:now_playing_file] has a non-boolean "
                    'value for the key "delayed"'
                )
        # Return errors, if any
        if len(errors) > 0:
            raise conf.InvalidConfigurationError(errors)
