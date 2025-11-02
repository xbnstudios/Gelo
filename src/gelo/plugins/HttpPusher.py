import gelo.arch
import gelo.conf
import gelo.mediator
import queue
import logging
import requests
from requests.adapters import HTTPAdapter, Retry
from threading import Timer


class HttpPusher(gelo.arch.IMarkerSink):
    """Push the marker to an HTTP endpoint."""

    PLUGIN_MODULE_NAME = "HttpPusher"
    HTTP_TIMEOUT_SECS = 5

    def __init__(self, config, mediator: gelo.arch.IMediator, show: str):
        """Create a new HttpPusher."""
        super().__init__(config, mediator, show)
        self.log = logging.getLogger("gelo.plugins.HttpPusher")
        self.validate_config()
        self.log.debug("Configuration valid")
        self.webhooks = self.config["webhooks"]
        self.delayed = self.config["delayed"]
        show_split = show.split("-")
        if len(show_split) < 2:
            self.log.warning(
                "Show argument on console not in the form of slug-###, "
                "using default values"
            )
            self.show_slug = "default"
            self.show_episode = "1"
        else:
            self.show_slug = show_split[0]
            self.show_episode = show_split[1]
        for webhook in self.webhooks:
            if "extra_delay" in self.webhooks[webhook]:
                self.webhooks[webhook]["extra_delay"] = float(
                    self.webhooks[webhook]["extra_delay"]
                )
        self.channel = self.mediator.subscribe(
            [gelo.arch.MarkerType.TRACK], HttpPusher.__name__, delayed=self.delayed
        )
        self.session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504, 429],
            raise_on_status=True,
            # False makes sure this retries for every method type, not just the
            # "safe" ones.
            allowed_methods=False,
        )
        self.session.mount("http://", HTTPAdapter(max_retries=retries))
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    def run(self):
        """Run the code that will send HTTP requests with the markers."""
        self.log.info("Starting plugin")
        while not self.should_terminate:
            try:
                marker = next(self.channel.listen())
                if not self.is_enabled:
                    continue
                self.log.debug("Received marker from channel: %s" % marker)
                self.request_all(marker)
            except queue.Empty:
                continue
            except gelo.mediator.UnsubscribeException:
                self.should_terminate = True

    def request_all(self, marker: gelo.arch.Marker):
        """Make HTTP requests to every webhook."""
        for name, options in self.webhooks.items():
            if "extra_delay" in options.keys():
                self.log.debug(
                    "Delaying marker for {} by {} seconds…".format(
                        name, options["extra_delay"]
                    )
                )
                delay = Timer(
                    options["extra_delay"], self.request, args=[marker, name, options]
                )
                delay.start()
            else:
                self.log.debug("Sending marker for {} immediately…".format(name))
                self.request(marker, name, options)

    def request(
        self, marker: gelo.arch.Marker, webhook_name: str, webhook_options: dict
    ):
        """Make one single HTTP request."""
        # Populate the payload object. Requests will turn this into form values for
        # POST and URL parameters for GET.
        payload = {webhook_options["marker_param"]: marker.label}
        # All of these are optional config keys.
        if "api_key_param" in webhook_options:
            # The config validator function checks to ensure api_key is present.
            payload[webhook_options["api_key_param"]] = webhook_options["api_key"]
        if "show_slug_param" in webhook_options:
            payload[webhook_options["show_slug_param"]] = self.show_slug
        if "show_episode_param" in webhook_options:
            payload[webhook_options["show_episode_param"]] = self.show_episode

        r = None
        attempts = 0
        while attempts < 3:
            attempts += 1
            try:
                if webhook_options["method"] == "GET":
                    self.log.warning(
                        "[{}] Non-repeatable GET requests are bad...".format(
                            webhook_name
                        )
                    )
                    r = self.session.get(
                        webhook_options["url"],
                        params=payload,
                        timeout=self.HTTP_TIMEOUT_SECS,
                    )
                    break
                elif webhook_options["method"] == "POST":
                    r = self.session.post(
                        webhook_options["url"],
                        data=payload,
                        timeout=self.HTTP_TIMEOUT_SECS,
                    )
                r.raise_for_status()
                self.log.info("Request to {} made successfully.".format(webhook_name))
                self.log.debug("Response data: {}".format(r.content))
                break
            except requests.ConnectionError as ce:
                self.log.warning(
                    "Connection Error while trying to make a request to"
                    "{}, attempt {}: {}".format(webhook_name, attempts, ce)
                )
                continue
            except requests.RequestException as re:
                self.log.warning(
                    "Non-retryable exception encountered while trying to make a "
                    "request to {}: {}".format(webhook_name, re)
                )
                break

    def validate_config(self):
        """Ensure the configuration file is valid."""
        errors = []

        if "delayed" not in self.config.keys():
            self.config["delayed"] = False
        else:
            if type(self.config["delayed"]) is not bool:
                errors.append(
                    '["plugin:HttpPusher"] has a non-boolean value for the key'
                    '"delayed"'
                )
        if "webhooks" not in self.config.keys():
            errors.append(
                '["plugin:HttpPusher"] is missing a webhooks table. Create a section '
                'titled ["plugin:HttpPusher".webhooks.your_webhook] and follow the '
                "example config."
            )
        else:
            for name, options in self.config["webhooks"].items():
                errors.extend(self.validate_config_for_webhook(options, name))
        if len(errors) > 0:
            raise gelo.conf.InvalidConfigurationError(errors)

    def validate_config_for_webhook(self, webhook_options: dict, webhook_name: str):
        """Ensure the portion of the configuration file for one webhook is valid."""
        errors = []
        if "url" not in webhook_options.keys():
            errors.append(
                (
                    '["plugin:HttpPusher".webhooks.{}] is missing the required '
                    'key "url"'
                ).format(webhook_name)
            )
        if "api_key_param" in webhook_options.keys():
            if "api_key" not in webhook_options.keys():
                errors.append(
                    (
                        '["plugin:HttpPusher".webhooks.{}] is missing the '
                        'required key "api_key"'
                    ).format(webhook_name)
                )
        if "method" not in webhook_options.keys():
            errors.append(
                (
                    '["plugin:HttpPusher".webhooks.{}] is missing the required '
                    'key "method"'
                ).format(webhook_name)
            )
        else:
            if webhook_options["method"] not in ["GET", "POST"]:
                errors.append(
                    (
                        '["plugin:HttpPusher".webhooks.{}] has an unsupported '
                        'HTTP method listed for the key "method". Choose GET or POST.'
                    ).format(webhook_name)
                )
        if "marker_param" not in webhook_options.keys():
            errors.append(
                (
                    '["plugin:HttpPusher".webhooks.{}] is missing the required '
                    'key "marker_param"'
                ).format(webhook_name)
            )
        if "extra_delay" in webhook_options.keys():
            if type(webhook_options["extra_delay"]) is not float:
                errors.append(
                    (
                        '["plugin:HttpPusher".webhooks.{}] has a non-float '
                        'value for the key "extra_delay"'
                    ).format(webhook_name)
                )
        return errors
