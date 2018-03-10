# -*- coding: utf-8 -*-
import threading

class IMarkerSource(Thread):
    """An interface defining the required methods of a marker source."""

    def __init__(self, config, mediator):
        self.config = config
        self.mediator = mediator

    def run(self):
        pass


class IMarkerSink(Thread):
    """An interface defining the required methods of a marker sink."""
    
    def __init__(self, config, mediator):
        self.config = config
        self.mediator = mediator

    def run(self):
        pass

    def notify(self, event_type, event_msg: str, timestamp):
        pass

class Mediator:
    """A middle layer that accepts events from sources and sends them to sinks.
    """

    def __init__(self):
        pass

    def publish(self, event_type, event_msg):
        pass

    def subscribe(self, event_types: list):
        pass
