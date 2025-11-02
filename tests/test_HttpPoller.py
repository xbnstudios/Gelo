from gelo.plugins import HttpPoller


class TestHttpPoller:
    def test_match_emdash_labels(self):
        tests = [
            ("Bill Withers", None),
            ("Not An - Em Dash", None),
            ("Au5 — Starflame", ("Au5", "Starflame")),
            ("Saint Motel — Van Horn", ("Saint Motel", "Van Horn")),
            ("Yasué — Native Mind", ("Yasué", "Native Mind")),
            (
                "Niko B — Why's this dealer? (Original Mix)",
                ("Niko B", "Why's this dealer? (Original Mix)"),
            ),
            ("菅野よう子 — エンカ", ("菅野よう子", "エンカ")),
        ]

        for testcase in tests:
            input = testcase[0]
            expected = testcase[1]
            result = HttpPoller.match_artist_track(input)
            assert result == expected
