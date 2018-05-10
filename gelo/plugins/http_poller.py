import re
import requests
import requests.exceptions
from gelo import arch, conf
from time import time, sleep


class HttpPoller(arch.IMarkerSource):
    """Poll an HTTP server of some description for markers."""

    PLUGIN_MODULE_NAME = 'http_poller'

    def __init__(self, config, mediator: arch.IMediator, show: str):
        """Create a new instance of HttpPoller."""
        super().__init__(config, mediator, show)
        self.last_marker = ''
        self.config_test()
        self.poll_url = self.config['poll_url']
        self.prefix_file = self.config['prefix_file']
        # Match anything inside parenthesis
        self.special_matcher = re.compile(r".*\((.*)\).*")

    def run(self):
        """Run the code that creates markers from the HTTP server.
        This should be run as a thread."""
        starttime = time()
        while not self.should_terminate:
            sleep(0.25 - ((time() - starttime) % 0.25))
            if not self.is_enabled:
                continue
            try:
                track = self.poll_server()
            except requests.exceptions.ConnectionError:
                continue
            if track == self.last_marker:
                continue
            m = arch.Marker(track)
            m.special = self.check_prefix_file()
            self.mediator.publish(arch.MarkerType.TRACK, m)
            self.last_marker = track

    def poll_server(self) -> str:
        """Connect to the HTTP server and request the current track.
        :return: Whatever the server responded with
        """
        return requests.get(self.poll_url).text.strip()

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
        if 'poll_url' not in self.config:
            errors.append('[plugin:icecast] does not have the required key'
                          ' "poll_url"')
        if 'prefix_file' not in self.config:
            errors.append('[plugin:icecast] does not have the required key'
                          ' "prefix_file"')
        # Throw exception if necessary.
        if len(errors) > 0:
            raise conf.InvalidConfigurationError(errors)
