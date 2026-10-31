"""merge() combines duplicate rows the same way the UI does."""
import unittest

import torrent_search as ts

MAGNET = "magnet:?xt=urn:btih:" + "c" * 40
PAGE = "https://www.limetorrents.lol/sintel-torrent-1.html"


class MergeSourcesTest(unittest.TestCase):
    def test_sources_and_max_counts(self):
        rows = ts.merge([
            ts.row("Sintel 1080p", 1000, 40, 2, "piratebay", MAGNET, "trusted"),
            ts.row("sintel", -1, 10, 9, "nyaa", MAGNET, "", 500),
            ts.row("Sintel", 1000, 5, 1, "nyaa", MAGNET),
        ])
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(r["sources"], ["piratebay", "nyaa"])
        self.assertEqual((r["seeds"], r["leech"], r["downloads"], r["trust"]), (40, 9, 500, "trusted"))
        self.assertEqual((r["name"], r["engine"], r["size"]), ("Sintel 1080p", "piratebay", 1000))
        self.assertEqual(r["score"], ts.score(ts.row("x", 0, 40, 2, "x", MAGNET, "trusted")))

    def test_size_filled_from_other_copy(self):
        rows = ts.merge([ts.row("a", -1, 9, 0, "x", MAGNET), ts.row("a", 2048, 1, 0, "y", MAGNET)])
        self.assertEqual(rows[0]["size"], 2048)

    def test_inputs_not_mutated(self):
        row = ts.row("a", 1, 1, 0, "x", MAGNET)
        ts.merge([row, ts.row("a", 1, 2, 0, "y", MAGNET)])
        self.assertNotIn("sources", row)
        self.assertNotIn("score", row)

    def test_single_row_has_sources(self):
        rows = ts.merge([ts.row("a", 1, 1, 0, "limetorrents", PAGE)])
        self.assertEqual(rows[0]["sources"], ["limetorrents"])
        self.assertEqual(rows[0]["link"], PAGE)


if __name__ == "__main__":
    unittest.main()
