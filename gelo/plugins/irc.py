import gelo


class IRC(gelo.arch.IMarkerSink):
    PLUGIN_MODULE_NAME = 'irc'

    def __init__(self, config, mediator: gelo.arch.IMediator, show: str):
        super().__init__(config, mediator, show)
