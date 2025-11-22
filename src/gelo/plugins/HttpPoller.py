import re
import time
import logging
import requests
import dataclasses
import requests.exceptions
from typing import Optional, Callable
from gelo import arch, conf


@dataclasses.dataclass
class Track:
    artist: str = ""
    title: str = ""

    def __str__(self):
        return f"{self.artist} — {self.title}"


def icecast_status_to_track(status: dict) -> Optional[Track]:
    if type(status) is not dict or "icestats" not in status:
        return None
    icestats = status["icestats"]
    if type(icestats) is not dict or "source" not in icestats:
        return None
    source = icestats["source"]
    if type(source) is not dict:
        return None
    if "artist" not in source:
        return None
    if "title" not in source:
        return None
    return Track(str(source["artist"]), str(source["title"]))


def do_every(
    period: float, keep_going: Callable[[], bool], fn: Callable, *args, **kwargs
):
    def g_tick():
        t = time.time()
        while True:
            t += period
            yield max(t - time.time(), 0)

    g = g_tick()
    while keep_going():
        time.sleep(next(g))
        fn(*args, **kwargs)


class HttpPoller(arch.IMarkerSource):
    """Poll an HTTP server of some description for markers."""

    PLUGIN_MODULE_NAME = "HttpPoller"

    def __init__(self, config, mediator: arch.IMediator, show: str):
        """Create a new instance of HttpPoller."""
        super().__init__(config, mediator, show)
        self.log = logging.getLogger("gelo.plugins.HttpPoller")
        self.last_track = Track()
        self.config_test()
        self.poll_url = self.config["poll_url"]
        self.prefix_file = self.config["prefix_file"]
        # Match anything inside parenthesis
        self.special_matcher = re.compile(r".*\((.*)\).*")

    def run(self):
        """Run the code that creates markers from the HTTP server.
        This should be run as a thread."""
        self.log.info("now running")
        starttime = time.time()

        def keep_going():
            return not self.should_terminate

        do_every(0.25, keep_going, self.run_cycle, starttime)

    def run_cycle(self, start_time: time.time):
        if not self.is_enabled:
            return
        try:
            icecast_status = self.poll_server()
            track = icecast_status_to_track(icecast_status)
        except requests.exceptions.ConnectionError as ce:
            self.log.info("connection error while polling server:", ce)
            return
        except requests.exceptions.JSONDecodeError as jde:
            self.log.info("invalid JSON returned by server:", jde)
            return
        if (
            not track
            or track == self.last_track
            or track.artist.strip() == ""
            or track.title.strip() == ""
        ):
            self.log.info("ignoring empty track metadata")
            return
        m = arch.Marker(str(track), track.artist, track.title)
        m.special = self.check_prefix_file()
        self.mediator.publish(arch.MarkerType.TRACK, m)
        self.last_track = track

    def poll_server(self) -> dict:
        """Connect to the HTTP server and request the current track.
        :return: Whatever the server responded with
        """
        return requests.get(self.poll_url).json()

    def check_prefix_file(self) -> str:
        """Check the prefix file to see if the track needs a special prefix.
        :return: The prefix, or None if there shouldn't be one."""
        try:
            with open(self.prefix_file, "r") as pf:
                first_line = pf.readline()
                g = self.special_matcher.match(first_line)
                return g.group(1) if g is not None else None
        except IOError:
            return None

    def config_test(self):
        """Test the configuration to ensure that it contains the required items.
        Also, convert any configuration items to the right formats, and perform
        variable expansions.
        """
        errors = []
        if "poll_url" not in self.config:
            errors.append('[plugin:icecast] does not have the required key "poll_url"')
        if "prefix_file" not in self.config:
            errors.append(
                '[plugin:icecast] does not have the required key "prefix_file"'
            )
        # Throw exception if necessary.
        if len(errors) > 0:
            raise conf.InvalidConfigurationError(errors)
