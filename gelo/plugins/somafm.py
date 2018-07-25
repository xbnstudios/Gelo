import re
import sys
import urllib.parse
from typing import Optional
from threading import Timer
import http.client
from gelo import arch, conf


class SomaFm(arch.IMarkerSource):
    """Connect to a Soma.FM stream and announce their markers."""

    PLUGIN_MODULE_NAME = 'somafm'
    HEADERS = {
        "Icy-MetaData": "1",
        "User-Agent": "gelo/3.2, somafm/1.0: https://github.com/s0ph0s-2/gelo"
    }

    def __init__(self, config, mediator: arch.IMediator, show: str):
        """Create a new instance of SomaFm."""
        super().__init__(config, mediator, show)
        self.last_track = ''
        self.http_client = None
        self.http_resp = None
        self.metadata_interval = 0
        self.config_test()
        self.url = self.config['stream_url']
        self.source_name = self.config['source_name']
        self.extra_delay = float(self.config['extra_delay'])

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
                m = arch.Marker(track)
                m.special = self.source_name
                delay = Timer(self.extra_delay,
                              self.mediator.publish,
                              args=[arch.MarkerType.TRACK, m])
                delay.start()
        self.teardown_connection()

    def setup_connection(self):
        """Connect to the configured stream."""
        parsed_url = urllib.parse.urlparse(self.url)
        if parsed_url.scheme == "http":
            self.http_client = http.client.HTTPConnection(parsed_url.netloc)
        elif parsed_url.scheme == "https":
            self.http_client = http.client.HTTPSConnection(parsed_url.netloc)
        else:
            print("could not identify url scheme")
            sys.exit(1)
        self.http_client.request("GET", parsed_url.path, headers=self.HEADERS)
        self.http_resp = self.http_client.getresponse()
        if self.http_resp is None:
            print("request failed")
            sys.exit(1)
        self.metadata_interval = int(self.http_resp.getheader("Icy-MetaInt"))

    def teardown_connection(self):
        """Disconnect from the configured stream."""
        self.http_client.close()

    def next_track(self) -> Optional[str]:
        """Get the next track.

        :returns: A string of the next track, or ``None`` if it hasn't
        changed yet.
        """
        ignored = self.http_resp.read(self.metadata_interval)
        size_byte = ord(self.http_resp.read(1))
        metadata_size = size_byte * 16
        metadata = str(self.http_resp.read(metadata_size), 'utf-8')
        if metadata == "":
            return None
        track_matcher = re.search("StreamTitle='([^']*)';", metadata)
        if track_matcher is None:
            return None
        track = track_matcher.group(1)
        if track is None:
            return None
        if track == self.last_track:
            return None
        self.last_track = track
        return track

    def config_test(self):
        """Verify this plugin's configuration."""
        errors = []
        if 'stream_url' not in self.config:
            errors.append('[plugin:somafm] does not have the required key'
                          ' "stream_url"')
        if 'source_name' not in self.config:
            errors.append('[plugin:somafm] does not have the required key'
                          ' "stream_url"')
        if 'extra_delay' not in self.config:
            errors.append('[plugin:somafm] does not have the required key'
                          ' "extra_delay"')
        elif not conf.is_float(self.config['extra_delay']):
            errors.append('[plugin:somafm] does not have a float value for'
                          ' the key "extra_delay"')
        if len(errors) > 0:
            raise conf.InvalidConfigurationError(errors)
