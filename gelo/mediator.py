import gelo.arch
import queue
import logging
from time import time
from threading import Lock
from functools import partial


class Mediator(gelo.arch.IMediator):
    """Accept from IMarkerSources and relay to IMarkerSinks."""

    QUEUE_MAX = 100

    def __init__(self):
        """Create a new instance of this Mediator."""
        super().__init__()
        self.channels = {}
        self.channel_lock = Lock()
        self.first_time = None
        self.log = logging.getLogger("gelo.mediator")

    def publish(self, marker_type: gelo.arch.MarkerType, marker:
                gelo.arch.Marker) -> None:
        """Publish a new event to all applicable subscribers.
        :marker_type: The EventType corresponding to the event
        :marker: The marker to publish"""
        if not marker_type:
            raise ValueError()
        if not marker:
            raise ValueError()
        self.log.info("Received new marker: %s" % marker)
        if self.first_time is None:
            t = time()
            self.log.debug("First time is none. Setting to %s" % t)
            self.first_time = t
        marker.time = time() - self.first_time
        if marker_type not in self.channels:
            self.channel_lock.acquire()
            if marker_type not in self.channels:
                self.channels[marker_type] = []
            self.channel_lock.release()
        self.log.debug("Pushing marker to queues for %s" % marker_type)
        for q in self.channels[marker_type]:
            if q.qsize() > self.QUEUE_MAX:
                q.put(None, block=False)
                continue
            q.put(marker, block=False)

    def subscribe(self, marker_types: gelo.arch.MarkerTypeList) -> queue.Queue:
        """Subscribe to all of the listed event types.
        :marker_types: A list of MarkerType types to subscribe to
        :return: A queue of markers"""
        if not marker_types:
            raise ValueError()
        if len(marker_types) < 1:
            raise ValueError()
        self.log.info("New subscriber to %s" % marker_types)
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

    def terminate(self):
        """Close all of the queues so the plugins can terminate."""
        self.channel_lock.acquire()
        for channel in self.channels:
            self.log.info("Terminating channel %s" % channel)
            for q in self.channels[channel]:
                q.put(None, block=False)

    @staticmethod
    def listen(q: queue.Queue, block=True, timeout=None):
        """Retrieve the next item from a queue."""
        while True:
            try:
                data = q.get(block=block, timeout=timeout)
            except queue.Empty:
                return
            if data is None:
                raise UnsubscribeException()
            yield data


class UnsubscribeException(Exception):
    """Raised when a queue is closing down and listeners should unsubscribe."""
    pass
