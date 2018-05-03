import gelo.arch
import gelo.plugins.irc
from time import sleep
from queue import Queue
from functools import partial
from configparser import ConfigParser


class TestMediator(gelo.arch.IMediator):
    """Mediator to test IRC."""

    def __init__(self):
        """Create the Mediator."""
        super().__init__()
        self.q = Queue()
        self.q.put(gelo.arch.Marker('ABBA - Money Money Money', 0.0))
        self.q.put(gelo.arch.Marker('John Travolta - Summer Lovin', 2.01))
        self.q.put(gelo.arch.Marker('Imperial Leisure - Man On The Street',
                                    3.84))
        self.q.put(gelo.arch.Marker('Zammuto - Need Some Sun', 6.23))
        self.q.put(gelo.arch.Marker('3typen - Pretty Little Thing', 7.98))
        self.q.put(gelo.arch.Marker('The Darkness - Forbidden Love', 9.59))
        self.q.put(gelo.arch.Marker('Justice - Fire', 13.01))
        self.q.listen = partial(self.listen, self.q)

    def subscribe(self, event_types: list):
        """Return the one queue that this Mediator creates."""
        return self.q

    def listen(self, q: Queue, block=True, timeout=5):
        """Wait for the next item off the queue."""
        sleep(2)
        yield q.get(block=block, timeout=timeout)


def main():
    """Run the main test driver"""
    c = ConfigParser()
    c['DEFAULT']['nick'] = 'gelo'
    c['DEFAULT']['server'] = 'localhost'
    c['DEFAULT']['port'] = '6667'
    c['DEFAULT']['tls'] = 'False'
    c['DEFAULT']['send_to'] = '#test'
    c['DEFAULT']['message'] = 'Now Playing: {marker}'
    tm = TestMediator()

    t = gelo.plugins.irc.IRC(c['DEFAULT'], tm, 'fnt-200')
    t.start()
    sleep(20)
    t.exit()


if __name__ == "__main__":
    main()
