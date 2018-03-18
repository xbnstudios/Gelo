# -*- coding: utf-8 -*-
from enum import Enum
from typing import List
from threading import Thread
from yapsy.IPlugin import IPlugin


class MarkerType(Enum):
    """Types of markers.
    TRACK is a song played over the air.
    TOPIC is a topic of conversation, be it an article or otherwise.
    """
    TRACK = 1
    TOPIC = 2


# A type for a list of MarkerType
MarkerTypeList = List[MarkerType]


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


class IMediator(object):
    """A middle layer that accepts events from sources and sends them to sinks.
    """

    def __init__(self):
        """Create a new mediator."""
        super().__init__()

    def publish(self, event_type: MarkerType, event_label: str) -> None:
        """Publish a new event to all applicable subscribers.
        :event_type: The EventType corresponding to the event
        :event_label: The actual text of the event"""
        pass

    def subscribe(self, event_types: MarkerTypeList):
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
