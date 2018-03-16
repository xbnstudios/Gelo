from gelo.architecture import IMediator, MarkerType
from gelo.plugins.icecast import Icecast
from configparser import ConfigParser
# import pydevd
# pydevd.settrace('localhost', port=9999, stdoutToServer=True,
#                 stderrToServer=True)


class TestMediator(IMediator):
    """Test Mediator, which just prints out the tracks it's notified of."""

    def notify(self, marker_type: MarkerType, marker: str):
        print(marker_type, marker)


def main():
    config = ConfigParser()
    config['DEFAULT']['port'] = '8080'
    config['DEFAULT']['bind_address'] = '127.0.0.1'
    config['DEFAULT']['source_password'] = 'correct-horse-battery-staple'
    config['DEFAULT']['num_clients'] = '3'
    config['DEFAULT']['basedir'] = '/Users/s0ph0s/.config/gelo/icecast'
    config['DEFAULT']['config_file'] = '/Users/s0ph0s/.config/gelo/icecast.xml'
    config['DEFAULT']['unprivileged_user'] = 's0ph0s'
    config['DEFAULT']['unprivileged_group'] = 'staff'

    tm = TestMediator()
    plugin = Icecast(config['DEFAULT'], tm)
    plugin.start()


if __name__ == "__main__":
    main()
