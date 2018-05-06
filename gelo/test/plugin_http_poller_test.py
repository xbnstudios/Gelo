from gelo.arch import IMediator, MarkerType, Marker
from gelo.plugins.http_poller import HttpPoller
from configparser import ConfigParser


class TestMediator(IMediator):
    """Test Mediator, which just prints out the tracks it's notified of."""

    def publish(self, marker_type: MarkerType, marker: Marker):
        print(marker_type, marker)


def main():
    config = ConfigParser()
    config['DEFAULT']['poll_url'] = 'http://localhost:8080/nowplaying.xsl'
    config['DEFAULT']['prefix_file'] = '/tmp/prefix.txt'

    tm = TestMediator()
    plugin = HttpPoller(config['DEFAULT'], tm, 'fnt-200')
    plugin.start()


if __name__ == "__main__":
    main()
