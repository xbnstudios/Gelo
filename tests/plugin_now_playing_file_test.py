from time import sleep
from functools import partial
from queue import Queue
from gelo.plugins.NowPlayingFile import NowPlayingFile
from gelo.arch import IMediator
from configparser import ConfigParser


class TestMediator(IMediator):
    """Mediator to test NowPlayingFile."""

    def __init__(self):
        """Create the Mediator."""
        super().__init__()
        self.q = Queue()
        self.q.put("ABBA - Money Money Money")
        self.q.put("John Travolta - Summer Lovin")
        self.q.put("Imperial Leisure - Man On The Street")
        self.q.put("Zammuto - Need Some Sun")
        self.q.put("3typen - Pretty Little Thing")
        self.q.put("The Darkness - Forbidden Love")
        self.q.put("Justice - Fire")
        self.q.listen = partial(self.listen, self.q)

    def subscribe(self, event_types: list):
        """Return the one queue that this Mediator creates."""
        return self.q

    def listen(self, q: Queue, block=True, timeout=None):
        """Wait for the next item off the queue."""
        sleep(2)
        yield q.get(block=block, timeout=timeout)


def main():
    """Run the main test driver"""
    c = ConfigParser()
    c["DEFAULT"]["path"] = "$HOME/Desktop/test.txt"
    tm = TestMediator()

    npf = NowPlayingFile(c["DEFAULT"], tm)
    npf.start()


if __name__ == "__main__":
    main()
