import pytest
from typing import Tuple
from gelo.arch import Marker
from gelo.plugins import HttpPusher
from gelo.mediator import Mediator
from gelo.conf import InvalidConfigurationError
from dataclasses import dataclass
from unittest.mock import Mock


@dataclass
class XTestCase:
    """The X is so that pytest doesn't try to collect it."""

    input: Tuple = ()
    output = None

    def __init__(self, input=(), output=None):
        self.input = input
        self.output = output


def mock_options(**kwargs):
    return dict(**kwargs)


def stub_config():
    return {
        "webhooks": {
            "example": {
                "url": "https://example.com/api/np",
                "method": "POST",
                "marker_param": "marker",
            }
        }
    }


class TestHttpPusher:
    def test_webhook_config(self):
        # Arrange
        mediator = Mock(spec=Mediator)
        show = "ex-1"
        none_config = stub_config()
        del none_config["webhooks"]["example"]["marker_param"]

        both_config = stub_config()
        both_config["webhooks"]["example"]["artist_param"] = "artist"
        both_config["webhooks"]["example"]["title_param"] = "title"

        just_artist = stub_config()
        del just_artist["webhooks"]["example"]["marker_param"]
        just_artist["webhooks"]["example"]["artist_param"] = "artist"

        just_title = stub_config()
        del just_title["webhooks"]["example"]["marker_param"]
        just_title["webhooks"]["example"]["title_param"] = "title"

        only_marker = stub_config()

        only_artist_title = stub_config()
        del only_artist_title["webhooks"]["example"]["marker_param"]
        only_artist_title["webhooks"]["example"]["artist_param"] = "artist"
        only_artist_title["webhooks"]["example"]["title_param"] = "title"

        # Act
        with pytest.raises(InvalidConfigurationError):
            _ = HttpPusher.HttpPusher(none_config, mediator, show)
        with pytest.raises(InvalidConfigurationError):
            _ = HttpPusher.HttpPusher(both_config, mediator, show)
        with pytest.raises(InvalidConfigurationError):
            _ = HttpPusher.HttpPusher(just_artist, mediator, show)
        with pytest.raises(InvalidConfigurationError):
            _ = HttpPusher.HttpPusher(just_title, mediator, show)
        m = HttpPusher.HttpPusher(only_marker, mediator, show)
        assert m is not None
        at = HttpPusher.HttpPusher(only_artist_title, mediator, show)
        assert at is not None

    def test_make_payload(self):
        ex_label = "Saint Motel — Van Horn"
        ex_artist = "Saint Motel"
        ex_title = "Van Horn"
        tests = [
            XTestCase(
                input=(mock_options(marker_param="np"), Marker(ex_label)),
                output={"np": ex_label},
            ),
            XTestCase(
                input=(
                    mock_options(artist_param="artist", title_param="title"),
                    Marker(ex_label, ex_artist, ex_title),
                ),
                output={"artist": ex_artist, "title": ex_title},
            ),
            XTestCase(
                input=(
                    mock_options(artist_param="artist", title_param="title"),
                    Marker(ex_label),
                ),
                output={"artist": "", "title": ex_label},
            ),
        ]

        mediator = Mock(spec=Mediator)
        config = stub_config()
        for testcase in tests:
            input = testcase.input
            expected = testcase.output

            cut = HttpPusher.HttpPusher(config, mediator, "ex-1")
            actual = cut.make_payload(input[0], input[1])

            assert actual == expected
