# -*- coding: utf-8 -*-
"""The overall architecture of Gelo.

This module includes the interfaces, enums, and value objects that are used
throughout the application.
"""

from enum import Enum
from threading import Thread


class MarkerType(Enum):
    """The types of markers that Gelo supports.

    It may be necessary to add additional marker types. I don't have a
    compelling reason to make this externally configurable right now, so if you
    have a good use case for another marker type (even just clearer semantics),
    open a GitHub issue (better yet, a PR) and I'll probably accept it.

    Enum values:
    :TRACK: a song played over the air.
    :TOPIC: a topic of conversation, be it an article or otherwise.
    """

    TRACK = 1
    TOPIC = 2

    @staticmethod
    def from_string(s: str):
        """Turn a string representation of a marker type into the enum value.

        Yes, this is implemented grossly (if..elif chain), but I can't define a
        class-level map for it, so I'm kinda stuck.

        :param s: The string to turn into a MarkerType.
        :returns: The appropriate MarkerType for ``s``, or None if invalid.
        """
        if s == "TRACK":
            return MarkerType.TRACK
        elif s == "TOPIC":
            return MarkerType.TOPIC
        else:
            return None


# A type for a list of MarkerType
MarkerTypeList = list[MarkerType]


class Marker(object):
    """A marker, or a label at a time.

    The time is a float number of seconds since the first marker."""

    def __init__(self, label: str, artist: str | None = None, title: str | None = None):
        """Create a new marker."""
        self.label = label
        self.artist = artist
        self.title = title
        self.time = None
        self.url = None
        self.special = None

    def __repr__(self):
        return "Marker(%s, %s, %s,  %s, %s, %s)" % (
            self.label,
            self.artist,
            self.title,
            self.time,
            self.special,
            self.url,
        )

    @classmethod
    def withtime(cls, label: str, time: float, **kwargs):
        """Create a marker with a time."""
        m = cls(label, **kwargs)
        m.time = time
        return m


# This class is defined here only so that the type hints work.
class IMarkerSink(Thread):
    pass


class IMediator(object):
    """A middle layer that accepts events from sources and sends them to sinks."""

    def __init__(self):
        """Create a new mediator."""
        super().__init__()

    def publish(self, event_type: MarkerType, event: Marker) -> None:
        """Publish a new event to all applicable subscribers.

        :event_type: The EventType corresponding to the event
        :event_label: The actual text of the event"""
        pass

    def subscribe(self, event_types: MarkerTypeList, subscriber: str, delayed=False):
        """Subscribe to all of the listed event types.
        :param event_types: The types of events to subscribe to
        :param subscriber: The name of the plugin that's subscribing to
        messages.  This should be the class name of the plugin, unless you
        :param delayed: Whether this subscriber should get markers as soon as
        they are published, or after the configured broadcast delay.
        like undefined behavior.
        """
        pass


class IMarkerSource(Thread):
    """An interface defining the required methods of a marker source."""

    PLUGIN_MODULE_NAME = None

    def __init__(self, config, mediator: IMediator, show: str):
        """Create a new marker source."""
        super().__init__()
        self.config = config
        self.mediator = mediator
        self.should_terminate = False
        self.show = show
        self.is_enabled = True

    def activate(self):
        """Activate the plugin by calling the start method.

        Implementers *should not* override this method unless they have a very
        good reason to. If it is necessary to override this method,
        implementers must call ``self.start()`` at some point, in order for
        the plugin thread to be created and run.
        """
        self.start()

    def run(self):
        """The main function of the plugin.

        Because plugins inherit from Thread, implementers *should* override
        this method to implement the functionality of their plugin.
        """
        pass

    def enable(self):
        """Enable the functionality of this plugin.

        Tell the plugin that it should do whatever it is it's supposed to be
        doing.
        """
        self.is_enabled = True

    def disable(self):
        """Disable the functionality of this plugin.

        Tell the plugin to stop doing whatever it is it's supposed to be doing.
        When in this disabled state, the plugin *should* continue consuming
        events from the event queue, but it *should not* act on them.
        """
        self.is_enabled = False

    def deactivate(self):
        """Deactivate the plugin.

        Because plugins are threaded, it may be necessary to call ``join()``
        on the plugin object after calling this method, in order to wait for
        the plugin to finish its work and stop.
        """
        self.should_terminate = True


class IMarkerSink(Thread):  # noqa: F811
    """An interface defining the required methods of a marker sink."""

    PLUGIN_MODULE_NAME = None

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
        self.is_enabled = True

    def activate(self):
        """Activate the plugin by calling the start method.

        Implementers *should not* override this method unless they have a very
        good reason to. If it is necessary to override this method,
        implementers must call ``self.start()`` at some point, in order for
        the plugin thread to be created and run.
        """
        self.start()

    def run(self):
        """The main function of the plugin.

        Because plugins inherit from Thread, implementers *should* override
        this method to implement the functionality of their plugin.
        """
        pass

    def enable(self):
        """Enable the functionality of this plugin.

        Tell the plugin that it should do whatever it is it's supposed to be
        doing.
        """
        self.is_enabled = True

    def disable(self):
        """Disable the functionality of this plugin.

        Tell the plugin to stop doing whatever it is it's supposed to be doing.
        When in this disabled state, the plugin *should* continue consuming
        events from the event queue, but it *should not* act on them.
        """
        self.is_enabled = False

    def deactivate(self):
        """Deactivate the plugin.

        Because plugins are threaded, it may be necessary to call ``join()`` on
        the plugin object after calling this method, in order to wait for the
        plugin to finish its work and stop. Note that because threads cannot be
        started again after they've been stopped, once a plugin is deactivated,
        it cannot be reactivated again without restarting the application.
        """
        self.should_terminate = True
