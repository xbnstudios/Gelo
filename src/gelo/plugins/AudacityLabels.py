import os
import queue
import logging
from gelo import arch, conf, mediator


class AudacityLabels(arch.IMarkerSink):
    """Write every MarkerType.TRACK marker to a CSV file, but with tabs."""

    PLUGIN_MODULE_NAME = "AudacityLabels"
    LINE_TEMPLATE = "{start}\t{finish}\t{label}\n"

    def __init__(self, config, mediator: arch.IMediator, show: str):
        """Create a new NowPlayingFile marker sink."""
        super().__init__(config, mediator, show)
        self.log = logging.getLogger("gelo.plugins.AudacityLabels")
        self.validate_config()
        self.log.debug("Configuration validated")
        self.collision_count = 0
        self.filename = self.avoid_overwrite_filename()
        self.log.info("Using %s as the data file path" % self.filename)
        self.delayed = self.config["delayed"]
        self.channel = self.mediator.subscribe(
            [arch.MarkerType.TRACK], AudacityLabels.__name__, delayed=self.delayed
        )
        self.last_marker = None

    def run(self):
        """Run the marker-receiving code."""
        while not self.should_terminate:
            try:
                current_marker = next(self.channel.listen())
                if not self.is_enabled:
                    continue
                self.log.debug("Received marker from channel: %s" % current_marker)
                if self.last_marker is not None:
                    line = self.create_line(current_marker, self.last_marker)
                    with open(self.filename, "a") as f:
                        f.write(line)
                    self.last_marker = current_marker
                else:
                    self.last_marker = current_marker
                    continue
            except queue.Empty:
                continue
            except mediator.UnsubscribeException:
                self.should_terminate = True
            except StopIteration:
                self.should_terminate = True
        if self.last_marker is not None:
            self.log.info("Writing final marker to file")
            with open(self.filename, "a") as f:
                f.write(
                    self.LINE_TEMPLATE.format(
                        start=self.last_marker.time,
                        finish=self.last_marker.time,
                        label=self.last_marker.label,
                    )
                )
                f.flush()
        else:
            self.log.warning("not writing final marker to file because it was None")

    def create_line(self, marker: arch.Marker, prev_marker: arch.Marker) -> str:
        """Create a line for the file using the current marker and the last one."""
        return self.LINE_TEMPLATE.format(
            start=prev_marker.time,
            finish=marker.time,
            label=prev_marker.label,
        )

    def avoid_overwrite_filename(self) -> str:
        """Come up with a file name to use for the labels.

        In order to avoid clobbering any data, this function increments the collision
        counter in the filename until the file no longer exists. This is a bit of a dumb
        algorithm, but hopefully the number of collisions (program restarts) will be
        small (< 3).

        If there is no collision avoidance marker in the filename, write a line to the
        end of the file which indicates the program was restarted.
        """
        # If there is no collision avoidance marker, write another entry that
        # says the program was restarted.
        if "{count}" not in self.config["path"]:
            self.log.info("Data file path missing {count} tag, writing restart marker")
            with open(self.config["path"], "a") as f:
                f.write(
                    self.LINE_TEMPLATE.format(
                        start=0, finish=0, label="PROGRAM RESTART"
                    )
                )
            return self.config["path"]
        # Otherwise, find the first unused filename.
        path = self.config["path"].format(show=self.show, count=self.collision_count)
        while os.path.exists(path):
            self.collision_count += 1
            path = self.config["path"].format(
                show=self.show, count=self.collision_count
            )
        return path

    def validate_config(self):
        """Ensure the configuration is valid, and perform path expansion."""
        errors = []
        if "path" not in self.config.keys():
            errors.append(
                '["plugin:AudacityLabels"] is missing the required key "path"'
            )
        else:
            self.config["path"] = os.path.expandvars(self.config["path"])
        if "delayed" not in self.config.keys():
            self.config["delayed"] = "False"
        else:
            if type(self.config["delayed"]) is not bool:
                errors.append(
                    '["plugin:AudacityLabels"] has a non-boolean '
                    'value for the key "delayed"'
                )
        # Return errors, if any
        if len(errors) > 0:
            raise conf.InvalidConfigurationError(errors)
