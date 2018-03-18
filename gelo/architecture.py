# -*- coding: utf-8 -*-
from enum import Enum
from threading import Thread
from yapsy.IPlugin import IPlugin


class MarkerType(Enum):
    """Types of markers.
    TRACK is a song played over the air.
    TOPIC is a topic of conversation, be it an article or otherwise.
    """
    TRACK = 1
    TOPIC = 2


class Marker(object):
    """A marker, or a label at a time.
    The time is a float number of seconds since the first marker."""
    def __init__(self, label: str, time: float):
        """Create a new marker."""
        self.label = label
        self.time = time


# This class is defined here only so that the type hints work.
class IMarkerSink(Thread, IPlugin):
    pass


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

    def subscribe(self, event_types: list):
        """Subscribe to all of the listed event types.
        :event_types: The types of events to subscribe to
        """
        pass


class IMarkerSource(Thread, IPlugin):
    """An interface defining the required methods of a marker source."""

    def __init__(self, config, mediator: IMediator):
        """Create a new marker source."""
        super().__init__()
        self.config = config
        self.mediator = mediator
        self.should_terminate = False

    def run(self):
        """Run the code that creates markers.
        This creates a thread."""
        pass

    def exit(self):
        """Terminate this thread."""
        self.should_terminate = True


class IMarkerSink(Thread, IPlugin):  # noqa: F811
    """An interface defining the required methods of a marker sink."""

    def __init__(self, config, mediator: IMediator, show: str):
        """Create a new marker sink.
        :config: The section of the configuration file for this plugin
        :mediator: The IMediator to get markers from
        :show: The short name of the show that the markers are for"""
        super().__init__()
        self.config = config
        self.mediator = mediator
        self.show = show
        self.should_terminate = False

    def run(self):
        """Run the code that will receive markers.
        This creates a thread."""
        pass

    def exit(self):
        """Terminate this thread."""
        self.should_terminate = True
