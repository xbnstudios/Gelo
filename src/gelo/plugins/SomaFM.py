import re
import logging
import urllib.parse
from typing import Optional
from threading import Timer
import http.client
from gelo import arch, conf


class SomaFM(arch.IMarkerSource):
    """Connect to a Soma.FM stream and announce their markers."""

    PLUGIN_MODULE_NAME = "SomaFM"
    HEADERS = {
        "Icy-MetaData": "1",
        "User-Agent": "gelo/3.2, somafm/1.0: https://github.com/s0ph0s-2/gelo",
    }

    def __init__(self, config, mediator: arch.IMediator, show: str):
        """Create a new instance of SomaFm."""
        super().__init__(config, mediator, show)
        self.last_track = ""
        self.http_client = None
        self.http_resp = None
        self.metadata_interval = 0
        self.log = logging.getLogger("gelo.plugins.somafm")
        self.config_test()
        self.url = self.config["stream_url"]
        self.source_name = self.config["source_name"]
        self.extra_delay = self.config["extra_delay"]
        self.marker_prefix = self.config["marker_prefix"].strip('"')
        self.is_enabled = not self.config["start_disabled"]

    def run(self):
        """Run the code that receives and posts markers.

        This should be run as a thread.
        """
        self.setup_connection()
        while not self.should_terminate:
            # This comes before the enabled check because otherwise the buffer
            # would fill up and eat memory.
            track = self.next_track()
            if not self.is_enabled:
                continue
            if track is not None:
                self.log.debug("track was not None; processing")
                m = arch.Marker(self.marker_prefix + track)
                m.special = self.source_name
                delay = Timer(
                    self.extra_delay,
                    self.mediator.publish,
                    args=[arch.MarkerType.TRACK, m],
                )
                delay.start()
                self.log.debug("started delayed track publish timer")
        self.teardown_connection()

    def setup_connection(self):
        """Connect to the configured stream."""
        self.log.debug("connecting to " + self.url)
        parsed_url = urllib.parse.urlparse(self.url)
        if parsed_url.scheme == "http":
            self.log.debug("using plaintext HTTP connection")
            self.http_client = http.client.HTTPConnection(parsed_url.netloc)
        elif parsed_url.scheme == "https":
            self.log.debug("using encrypted HTTPS connection")
            self.http_client = http.client.HTTPSConnection(parsed_url.netloc)
        else:
            self.log.warning("unsupported stream protocol; terminating")
            self.should_terminate = True
            return
        self.http_client.request("GET", parsed_url.path, headers=self.HEADERS)
        self.http_resp = self.http_client.getresponse()
        if self.http_resp is None:
            self.log.warning(
                "HTTP response was None. Is the stream configured properly?"
            )
            self.should_terminate = True
        self.metadata_interval = int(self.http_resp.getheader("Icy-MetaInt"))
        self.log.debug("metadata interval: " + str(self.metadata_interval) + " bytes")

    def teardown_connection(self):
        """Disconnect from the configured stream."""
        self.log.debug("tearing down connection")
        if self.http_client is not None:
            self.http_client.close()

    def next_track(self) -> Optional[str]:
        """Get the next track.

        :returns: A string of the next track, or ``None`` if it hasn't
        changed yet.
        """
        if self.http_resp is None:
            self.log.warning(
                "http_resp is null, so next_track was called before the connection was set up"
            )
            return None
        _ = self.http_resp.read(self.metadata_interval)
        size_byte = ord(self.http_resp.read(1))
        metadata_size = size_byte * 16
        self.log.debug("reading " + str(metadata_size) + " bytes of metadata")
        metadata = str(self.http_resp.read(metadata_size), "utf-8")
        self.log.debug("stringified metadata: " + metadata)
        if metadata == "":
            self.log.debug("metadata was empty; return None")
            return None
        track_matcher = re.search(r"StreamTitle='(.*?)';(\S|$)", metadata)
        if track_matcher is None:
            self.log.debug("metadata didn't contain StreamTitle; return None")
            return None
        track = track_matcher.group(1)
        if track is None:
            self.log.debug("match group 1 is None; return None")
            return None
        if track == self.last_track:
            self.log.debug("track identical to previous track; return None")
            return None
        self.log.info("New track: " + track)
        self.last_track = track
        return track

    def config_test(self):
        """Verify this plugin's configuration."""
        errors = []
        if "stream_url" not in self.config:
            errors.append('[plugin:SomaFM] does not have the required key "stream_url"')
        if "source_name" not in self.config:
            errors.append('[plugin:SomaFM] does not have the required key "stream_url"')
        if "extra_delay" not in self.config:
            errors.append(
                '[plugin:SomaFM] does not have the required key "extra_delay"'
            )
        elif type(self.config["extra_delay"]) is not float:
            errors.append(
                '[plugin:SomaFM] does not have a float value for the key "extra_delay"'
            )
        if "start_disabled" not in self.config:
            errors.append(
                '[plugin:SomaFM] does not have the required key "start_disabled"'
            )
        elif type(self.config["start_disabled"]) is not bool:
            errors.append(
                "[plugin:SomaFM] does not have a boolean"
                'value for the key "start_disabled"'
            )
        if "marker_prefix" not in self.config:
            errors.append(
                '[plugin:SomaFM] does not have the required key "marker_prefix"'
            )

        if len(errors) > 0:
            raise conf.InvalidConfigurationError(errors)
