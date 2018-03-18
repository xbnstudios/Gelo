import queue
from time import time
from threading import Lock
from functools import partial
from .arch import IMediator, MarkerType, MarkerTypeList, Marker


class Mediator(IMediator):
    """Accept from IMarkerSources and relay to IMarkerSinks."""

    QUEUE_MAX = 100

    def __init__(self):
        """Create a new instance of this Mediator."""
        super().__init__()
        self.channels = {}
        self.channel_lock = Lock()
        self.first_time = None

    def publish(self, marker_type: MarkerType, marker_label: str) -> None:
        """Publish a new event to all applicable subscribers.
        :marker_type: The EventType corresponding to the event
        :marker_label: The actual text of the event"""
        if not marker_type:
            raise ValueError()
        if not marker_label:
            raise ValueError()
        if self.first_time is None:
            self.first_time = time()
        marker = Marker(marker_label, time() - self.first_time)
        if marker_type not in self.channels:
            self.channel_lock.acquire()
            if marker_type not in self.channels:
                self.channels[marker_type] = []
            self.channel_lock.release()
        for q in self.channels[marker_type]:
            if q.qsize() > self.QUEUE_MAX:
                q.put(None, block=False)
                continue
            q.put(marker, block=False)

    def subscribe(self, marker_types: MarkerTypeList) -> queue.Queue:
        """Subscribe to all of the listed event types.
        :marker_types: A list of MarkerType types to subscribe to
        :return: A queue of markers"""
        if not marker_types:
            raise ValueError()
        if len(marker_types) < 1:
            raise ValueError()
        q = queue.Queue()
        q.listen = partial(self.listen, q)
        for marker_type in marker_types:
            if marker_type not in self.channels:
                self.channel_lock.acquire()
                if marker_type not in self.channels:
                    self.channels[marker_type] = []
                self.channel_lock.release()
            self.channels[marker_type].append(q)
        return q

    @staticmethod
    def listen(self, q: queue.Queue, block=True, timeout=5):
        """Retreive the next item from a queue."""
        while True:
            try:
                data = q.get(block=block, timeout=timeout)
            except queue.Empty:
                return
            if data is None:
                raise UnsubscribeException()
            yield data


class UnsubscribeException(Exception):
    """Raised when a queue should be unsubscribed from."""
    pass
