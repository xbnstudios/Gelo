from time import sleep
from functools import partial
from queue import Queue
from gelo.plugins.AudacityLabels import AudacityLabels
from gelo.arch import IMediator, Marker
from configparser import ConfigParser


class TestMediator(IMediator):
    """Mediator to test AudacityLabels."""

    def __init__(self):
        """Create the Mediator."""
        super().__init__()
        self.q = Queue()
        self.q.put(Marker("ABBA - Money Money Money", 0.0))
        self.q.put(Marker("John Travolta - Summer Lovin", 2.01))
        self.q.put(Marker("Imperial Leisure - Man On The Street", 3.84))
        self.q.put(Marker("Zammuto - Need Some Sun", 6.23))
        self.q.put(Marker("3typen - Pretty Little Thing", 7.98))
        self.q.put(Marker("The Darkness - Forbidden Love", 9.59))
        self.q.put(Marker("Justice - Fire", 13.01))
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
    c["DEFAULT"]["path"] = "$HOME/Desktop/{show}.csv"
    tm = TestMediator()

    al = AudacityLabels(c["DEFAULT"], tm, "fnt-200")
    al.start()
    sleep(20)
    al.exit()


if __name__ == "__main__":
    main()
