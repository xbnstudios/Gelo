import gelo.arch
import gelo.conf
import gelo.mediator
import queue
import logging
import requests


class HttpPusher(gelo.arch.IMarkerSink):
    """Push the marker to an HTTP endpoint."""

    PLUGIN_MODULE_NAME = 'http_pusher'

    def __init__(self, config, mediator: gelo.arch.IMediator, show: str):
        """Create a new HttpPusher."""
        super().__init__(config, mediator, show)
        self.log = logging.getLogger("gelo.plugins.HttpPusher")
        self.validate_config()
        self.log.debug("Configuration valid")
        self.url = self.config['url']
        self.method = self.config['method']
        self.api_key = self.config['api_key']
        self.api_key_param = self.config['api_key_param']
        self.marker_param = self.config['marker_param']
        self.delayed = gelo.conf.as_bool(self.config['delayed'])
        self.channel = self.mediator.subscribe([gelo.arch.MarkerType.TRACK],
                                               HttpPusher.__name__,
                                               delayed=self.delayed)
        self.session = requests.Session()

    def run(self):
        """Run the code that will send HTTP requests with the markers."""
        self.log.info("Starting plugin")
        while not self.should_terminate:
            try:
                marker = next(self.channel.listen())
                if not self.is_enabled:
                    continue
                self.log.debug("Received marker from channel: %s" % marker)
                self.request(marker)
            except queue.Empty:
                continue
            except gelo.mediator.UnsubscribeException:
                self.should_terminate = True

    def request(self, marker: gelo.arch.Marker):
        """Make the HTTP request."""
        payload = {
            self.marker_param: marker.label,
            self.api_key_param: self.api_key
        }
        r = None
        if self.method == "GET":
            self.log.warning("Non-repeatable GET requests are bad...")
            r = self.session.get(self.url, params=payload)
        elif self.method == "POST":
            r = self.session.post(self.url, data=payload)
        if r is not None and r.status_code == 200:
            self.log.info("Request made successfully.")
        elif r is not None:
            self.log.info("Request failed: %s" % r.text)
        else:
            self.log.info("Request failed: response object was None ("
                          "shouldn't happen)")

    def validate_config(self):
        """Ensure the configuration file is valid."""
        errors = []
        if 'url' not in self.config.keys():
            errors.append('[plugin:http_pusher] is missing the required key'
                          ' "url"')
        if 'api_key' not in self.config.keys():
            errors.append('[plugin:http_pusher] is missing the required key'
                          ' "api_key"')
        if 'method' not in self.config.keys():
            errors.append('[plugin:http_pusher] is missing the required key'
                          ' "method"')
        else:
            if self.config['method'] not in ['GET', 'POST']:
                errors.append('[plugin:http_pusher] has an unsupported HTTP '
                              'method listed for the key "method".')
        if 'api_key_param' not in self.config.keys():
            errors.append('[plugin:http_pusher] is missing the required key'
                          ' "api_key_param"')
        if 'marker_param' not in self.config.keys():
            errors.append('[plugin:http_pusher] is missing the required key'
                          ' "marker_param"')
        if 'delayed' not in self.config.keys():
            self.config['delayed'] = 'False'
        else:
            if not gelo.conf.is_bool(self.config['delayed']):
                errors.append('[plugin:http_pusher] has a non-boolean value '
                              'for the key "delayed"')
        if len(errors) > 0:
            raise gelo.conf.InvalidConfigurationError(errors)
