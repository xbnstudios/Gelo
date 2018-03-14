# -*- coding: utf-8 -*-
import threading

class IMediator:
    """A middle layer that accepts events from sources and sends them to sinks.
    """

    def __init__(self):
        """Create a new mediator."""
        pass

    def publish(self, event_type, event_msg):
        """Publish a new event via this mediator.
        :event_type: The type of the event
        :event_msg: The event string
        """
        pass

    def subscribe(self, event_types: list, subscriber: IMarkerSink):
        """Subscribe to all of the listed event types.
        :event_types: The types of events to subscribe to
        :subscriber: The subscriber to be notified
        """
        pass


class IMarkerSource(Thread):
    """An interface defining the required methods of a marker source."""

    def __init__(self, config, mediator: IMediator):
        """Create a new marker source."""
        self.config = config
        self.mediator = mediator

    def run(self):
        """Run the code that creates markers.
        This creates a thread."""
        pass


class IMarkerSink(Thread):
    """An interface defining the required methods of a marker sink."""

    def __init__(self, config, mediator: IMediator):
        """Create a new marker sink."""
        self.config = config
        self.mediator = mediator

    def run(self):
        """Run the code that will receive markers.
        This creates a thread."""
        pass

    def notify(self, event_type, event_msg: str, timestamp):
        """The function that the Mediator will call to give this sink an event.
        :event_type: The type of the event
        :event_msg: The event string
        :timestamp: How long it's been (wall-clock time) since the first marker
        """
        pass
