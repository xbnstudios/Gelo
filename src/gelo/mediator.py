import gelo.arch
import queue
import logging
from time import time
from threading import Lock, Timer


class ListenableQueue(queue.Queue):
    def listen(self, block=True, timeout=None):
        """Retrieve the next item from a queue."""
        while True:
            try:
                data = self.get(block=block, timeout=timeout)
            except queue.Empty:
                return
            if data is None:
                raise UnsubscribeException()
            yield data


class Mediator(gelo.arch.IMediator):
    """Accept from IMarkerSources and relay to IMarkerSinks."""

    QUEUE_MAX = 100

    def __init__(self, broadcast_delay: float):
        """Create a new instance of this Mediator."""
        super().__init__()
        self.instant_channels = {}
        self.delayed_channels = {}
        self.subscriber_map = {}
        self.instant_channel_lock = Lock()
        self.delayed_channel_lock = Lock()
        self.subscriber_lock = Lock()
        self.first_time = None
        self.shouldSquelchNext = False
        self.stopped = False
        self.broadcast_delay = broadcast_delay
        self.log = logging.getLogger("gelo.mediator")

    def publish(
        self, marker_type: gelo.arch.MarkerType, marker: gelo.arch.Marker
    ) -> None:
        """Publish a new event to all applicable subscribers.
        :marker_type: The EventType corresponding to the event
        :marker: The marker to publish"""
        if not marker_type:
            raise ValueError()
        if not marker:
            raise ValueError()
        self.log.info("Received new marker: %s" % marker)
        if self.shouldSquelchNext:
            self.log.debug("Ignoring marker because squelch")
            self.shouldSquelchNext = False
            return
        if self.stopped:
            self.log.debug("Ignoring marker because stopped")
            return
        if self.first_time is None:
            t = time()
            self.log.debug("First time is none. Setting to %s" % t)
            self.first_time = t
        marker.time = time() - self.first_time
        delay = Timer(self.broadcast_delay, self._publish, args=[marker_type, marker])
        delay.start()
        self.log.info("Broadcast delay started.")
        if marker_type not in self.instant_channels:
            self.instant_channel_lock.acquire()
            if marker_type not in self.instant_channels:
                self.instant_channels[marker_type] = []
            self.instant_channel_lock.release()
        self.log.debug("Pushing marker to instant queues for %s" % marker_type)
        for q in self.instant_channels[marker_type]:
            if q.qsize() > self.QUEUE_MAX:
                q.put(None, block=False)
                continue
            q.put(marker, block=False)

    def _publish(
        self, marker_type: gelo.arch.MarkerType, marker: gelo.arch.Marker
    ) -> None:
        """Publish markers to delayed subscribers.

        This is designed to be called by a threading.Timer, so that the
        actual marker output occurs somewhat in-line with the actual broadcast.

        :param marker_type: The EventType corresponding to this marker.
        :param marker: The Marker to publish.
        """
        if marker_type not in self.delayed_channels:
            self.delayed_channel_lock.acquire()
            if marker_type not in self.delayed_channels:
                self.delayed_channels[marker_type] = []
            self.delayed_channel_lock.release()
        self.log.debug("Pushing marker to delayed queues for %s" % marker_type)
        for q in self.delayed_channels[marker_type]:
            if q.qsize() > self.QUEUE_MAX:
                q.put(None, block=False)
                continue
            q.put(marker, block=False)

    def subscribe(
        self, marker_types: gelo.arch.MarkerTypeList, subscriber: str, delayed=False
    ) -> ListenableQueue:
        """Subscribe to all of the listed event types.
        :param marker_types: A list of MarkerType types to subscribe to.
        :param subscriber: The class name of the subscriber.
        :param delayed: Whether this subscriber should get markers as soon as
        they are published, or after the configured broadcast delay.
        :return: A queue of markers
        """
        if not marker_types:
            raise ValueError()
        if len(marker_types) < 1:
            raise ValueError()
        if not subscriber:
            raise ValueError()
        self.log.info("New subscriber to %s: %s" % (marker_types, subscriber))
        q = ListenableQueue()
        if delayed:
            for marker_type in marker_types:
                if marker_type not in self.delayed_channels:
                    self.delayed_channel_lock.acquire()
                    if marker_type not in self.delayed_channels:
                        self.delayed_channels[marker_type] = []
                    self.delayed_channel_lock.release()
                self.delayed_channels[marker_type].append(q)
        else:
            for marker_type in marker_types:
                if marker_type not in self.instant_channels:
                    self.instant_channel_lock.acquire()
                    if marker_type not in self.instant_channels:
                        self.instant_channels[marker_type] = []
                    self.instant_channel_lock.release()
                self.instant_channels[marker_type].append(q)
        self.subscriber_lock.acquire()
        self.subscriber_map[subscriber] = q
        self.subscriber_lock.release()
        return q

    def terminate(self):
        """Close all of the queues so the plugins can terminate."""
        self.instant_channel_lock.acquire()
        for channel in self.instant_channels:
            self.log.info("Terminating instant channel %s" % channel)
            for q in self.instant_channels[channel]:
                q.put(None, block=False)
        self.instant_channel_lock.release()
        self.delayed_channel_lock.acquire()
        for channel in self.delayed_channels:
            self.log.info("Terminating delayed channel %s" % channel)
            for q in self.delayed_channels[channel]:
                q.put(None, block=False)
        self.delayed_channel_lock.release()

    def close_subscriber(self, subscriber: str):
        """Close the queue for a given subscriber.

        :param subscriber: The class name of the subscriber to close the
        queue for.
        """
        self.subscriber_lock.acquire()
        self.subscriber_map[subscriber].put(None, block=False)
        self.subscriber_lock.release()


class UnsubscribeException(Exception):
    """Raised when a queue is closing down and listeners should unsubscribe."""

    pass
