from gelo.architecture import IMediator

class Icecast(IMarkerSource):
    """Fork an Icecast server in order to capture chapter marks"""
    
    def __init__(self, config, mediator: gelo.architecture.IMediator):
        """Create a new instance of Icecast (the plugin)."""
        self.mediator = mediator

    def run(self):
        """Run the code that creates markers from Traktor's stream.
        This should be run as a thread."""

