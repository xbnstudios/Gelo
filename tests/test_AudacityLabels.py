from unittest import mock
from tempfile import NamedTemporaryFile
from time import sleep
from configparser import ConfigParser
from gelo.plugins import AudacityLabels
from gelo import arch, mediator


class TestAudacityLabels:
    def test_happy_path(self):
        markers = [
            arch.Marker.withtime("ABBA - Money Money Money", 0.1),
            arch.Marker.withtime("John Travolta - Summer Lovin", 0.2),
            arch.Marker.withtime("Imperial Leisure - Man On The Street", 0.3),
            arch.Marker.withtime("Zammuto - Need Some Sun", 0.4),
            arch.Marker.withtime("3typen - Pretty Little Thing", 0.5),
            arch.Marker.withtime("The Darkness - Forbidden Love", 0.6),
            arch.Marker.withtime("Justice - Fire", 0.7),
        ]
        m = mock.create_autospec(mediator.Mediator)
        q = mock.create_autospec(mediator.ListenableQueue)
        q.listen = mock.Mock(return_value=iter(markers))
        m.subscribe = mock.Mock(return_value=q)
        c = ConfigParser()
        with NamedTemporaryFile(suffix=".csv") as out_csv:
            c["DEFAULT"]["path"] = str(out_csv.name)
            al = AudacityLabels.AudacityLabels(c["DEFAULT"], m, "fnt-200")
            al.start()
            sleep(0.8)
            al.should_terminate = True
            al.join()
            contents = b"".join(out_csv.readlines())
            with open("testdata/audacitylabels.csv", "rb") as expected_file:
                expected = b"".join(expected_file.readlines())
                assert contents == expected
