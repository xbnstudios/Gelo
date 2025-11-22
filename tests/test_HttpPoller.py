import responses
import requests
import unittest
from responses.registries import OrderedRegistry
from unittest import mock
from gelo.plugins import HttpPoller
from gelo import arch, mediator

STATUS_HTML = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <title>Icecast Streaming Media Server</title>
    <link rel="stylesheet" type="text/css" href="style.css" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes" />
  </head>
  <body><h1 id="header">Icecast2 Status</h1><div id="menu"><ul><li><a href="admin/">Administration</a></li><li><a href="status.xsl">Server Status</a></li><li><a href="server_version.xsl">Version</a></li></ul></div>
        <!-- WARNING:
         DO NOT ATTEMPT TO PARSE ICECAST HTML OUTPUT!
         The web interface may change completely between releases.
         If you have a need for automatic processing of server data,
         please read the appropriate documentation. Latest docs:
         https://icecast.org/docs/icecast-latest/icecast2_stats.html
        -->
        <div class="roundbox"><div class="mounthead"><h3 class="mount">Mount Point /traktor</h3><div class="right"><ul class="mountlist"><li><a class="play" href="/traktor.m3u">M3U</a></li><li><a class="play" href="/traktor.xspf">XSPF</a></li></ul></div></div><div class="mountcont"><div class="audioplayer"><audio controls="controls" preload="none"><source src="/traktor" type="application/ogg"></source></audio></div><table class="yellowkeys"><tbody><tr><td>Stream Name:</td><td>Traktor Stream</td></tr><tr><td>Stream Description:</td><td>Traktor Stream</td></tr><tr><td>Content Type:</td><td>application/ogg</td></tr><tr><td>Stream started:</td><td class="streamstats">Fri, 21 Nov 2025 19:06:55 -0500</td></tr><tr><td>Bitrate:</td><td class="streamstats">Quality 0</td></tr><tr><td>Listeners (current):</td><td class="streamstats">0</td></tr><tr><td>Listeners (peak):</td><td class="streamstats">0</td></tr><tr><td>Genre:</td><td class="streamstats">Mixed Styles</td></tr><tr><td>Stream URL:</td><td class="streamstats"><a href="localhost">localhost</a></td></tr><tr><td>Currently playing:</td><td class="streamstats">The Killers -
                                                                The Man</td></tr></tbody></table></div></div><div id="footer">
                Support icecast development at <a href="https://www.icecast.org/">www.icecast.org</a></div></body>
</html>"""


def fake_config(
    poll_url="http://example.com/status-json.xsl",
    prefix_file="/home/paradox/nowplaying.txt",
):
    return {
        "poll_url": poll_url,
        "prefix_file": prefix_file,
    }


def icestats(artist: str, title: str) -> dict:
    return {
        "icestats": {
            "source": {
                "artist": artist,
                "title": title,
            }
        }
    }


def check_marker(expected: (str, str, str), actual):
    assert len(actual.args) == 2
    assert actual.args[0] == arch.MarkerType.TRACK
    marker = actual.args[1]
    assert marker.label == expected[0]
    assert marker.artist == expected[1]
    assert marker.title == expected[2]


class TestHttpPoller:
    def test_icecast_status_to_track(self):
        """Confirm that icecast_status_to_track is robust against a variety of bad inputs."""
        tests = [
            ({}, None),
            ([], None),
            ({"icestats": 0}, None),
            ({"icestats": {}}, None),
            ({"icestats": {"source": "foo"}}, None),
            ({"icestats": {"source": {}}}, None),
            ({"icestats": {"source": {"artist": "foo"}}}, None),
            ({"icestats": {"source": {"title": "foo"}}}, None),
            (
                {"icestats": {"source": {"artist": "bar", "title": "foo"}}},
                HttpPoller.Track("bar", "foo"),
            ),
        ]
        for testcase in tests:
            input = testcase[0]
            expected = testcase[1]
            result = HttpPoller.icecast_status_to_track(input)
            assert result == expected

    @responses.activate
    def test_run_cycle_basic(self):
        """Confirm that run_cycle handles basic error conditions and the happy path."""
        notfound = "http://example.com/notfound"
        broken = "http://example.com/broken"
        invalidjson = "http://example.com/status.xsl"
        array = "http://example.com/array"
        working = "http://example.com/status-json.xsl"
        responses.add(responses.GET, notfound, status=404)
        responses.add(responses.GET, broken, body=requests.ConnectionError("foo"))
        responses.add(responses.GET, invalidjson, body=STATUS_HTML)
        responses.add(responses.GET, array, json=[])
        responses.add(
            responses.GET,
            working,
            json=icestats("Tom Cardy", "Hey, I Don't Work Here"),
        )

        tests = [
            (notfound, None),
            (broken, None),
            (invalidjson, None),
            (array, None),
            (
                working,
                (
                    "Tom Cardy — Hey, I Don't Work Here",
                    "Tom Cardy",
                    "Hey, I Don't Work Here",
                ),
            ),
        ]
        for testcase in tests:
            input = testcase[0]
            expected = testcase[1]
            m = mock.create_autospec(mediator.Mediator)

            config = fake_config(poll_url=input)
            cut = HttpPoller.HttpPoller(
                config,
                m,
                "ex-1",
            )
            cut.run_cycle(0)
            if expected is None:
                assert not m.publish.called
            else:
                assert m.publish.called
                pub_args = m.publish.call_args
                assert pub_args is not None
                assert pub_args.args is not None
                check_marker(expected, pub_args)

    @responses.activate(registry=OrderedRegistry)
    def test_run_cycle_skips_duplicate(self):
        """Confirm that run_cycle skips duplicate values."""
        # Arrange
        poll_url = "http://example.com/status-json.xsl"
        a = "Screamarts"
        t1 = "Resonant Stride (Original Mix)"
        t2 = "Cultus (Original Mix)"
        expected1 = (f"{a} — {t1}", a, t1)
        expected2 = (f"{a} — {t2}", a, t2)
        responses.get(poll_url, json=icestats(a, t1))
        responses.get(poll_url, json=icestats(a, t2))
        responses.get(poll_url, json=icestats(a, t2))
        responses.get(poll_url, json=icestats(a, t2))
        m = mock.create_autospec(mediator.Mediator)
        config = fake_config(poll_url=poll_url)
        cut = HttpPoller.HttpPoller(
            config,
            m,
            "ex-1",
        )

        # Act
        cut.run_cycle(0)
        cut.run_cycle(0)
        cut.run_cycle(0)
        cut.run_cycle(0)

        # Assert
        call_args_list = m.publish.call_args_list
        assert len(call_args_list) == 2
        check_marker(expected1, call_args_list[0])
        check_marker(expected2, call_args_list[1])

    @responses.activate(registry=OrderedRegistry)
    def test_run_cycle_skips_empty(self):
        """Confirm that run_cycle skips empty values."""
        # Arrange
        poll_url = "http://example.com/status-json.xsl"
        a = "Screamarts"
        t1 = "Resonant Stride (Original Mix)"
        t2 = "Cultus (Original Mix)"
        expected1 = (f"{a} — {t1}", a, t1)
        expected2 = (f"{a} — {t2}", a, t2)
        responses.get(poll_url, json=icestats("", ""))
        responses.get(poll_url, json=icestats(a, t1))
        responses.get(poll_url, json=icestats("", ""))
        responses.get(poll_url, json=icestats(a, t2))
        responses.get(poll_url, json=icestats(a, t2))
        m = mock.create_autospec(mediator.Mediator)
        config = fake_config(poll_url=poll_url)
        cut = HttpPoller.HttpPoller(
            config,
            m,
            "ex-1",
        )

        # Act
        cut.run_cycle(0)
        cut.run_cycle(0)
        cut.run_cycle(0)
        cut.run_cycle(0)
        cut.run_cycle(0)

        # Assert
        call_args_list = m.publish.call_args_list
        assert len(call_args_list) == 2
        check_marker(expected1, call_args_list[0])
        check_marker(expected2, call_args_list[1])
