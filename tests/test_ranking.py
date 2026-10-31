"""Unit tests for score, merge and size parsing (no network, no plugins)."""
import unittest

import torrent_search as ts

HASH_A = "a" * 40
HASH_B = "b" * 40


def r(seeds=0, leech=0, downloads=None, trust="", link=None, engine="x", name="ubuntu-24.04-desktop-amd64.iso"):
    return ts.row(name, 1024, seeds, leech, engine, link or f"magnet:?xt=urn:btih:{HASH_A}", trust, downloads)


class ScoreTest(unittest.TestCase):
    def test_seeds_and_leech(self):
        self.assertEqual(ts.score(r(seeds=100, leech=40)), 110.0)

    def test_downloads_are_log_scaled(self):
        self.assertEqual(ts.score(r(downloads=999)), 30.0)

    def test_trust_weights(self):
        base = ts.score(r(seeds=100))
        for trust, weight in ts.TRUST_WEIGHT.items():
            with self.subTest(trust=trust):
                self.assertEqual(ts.score(r(seeds=100, trust=trust)), round(base * weight, 1))

    def test_unknown_trust_is_neutral(self):
        self.assertEqual(ts.score(r(seeds=100, trust="member")), 100.0)

    def test_unknown_peer_counts_count_as_zero(self):
        # archive.org has no peer counts and reports -1
        self.assertEqual(ts.score(r(seeds=-1, leech=-1)), 0.0)
        self.assertEqual(ts.score(r(seeds=-1, leech=-1, downloads=99)), 20.0)


class MergeTest(unittest.TestCase):
    def test_same_infohash_keeps_best(self):
        low = r(seeds=5, engine="rutor")
        high = r(seeds=50, engine="piratebay")
        rows = ts.merge([low, high])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["engine"], "piratebay")

    def test_infohash_is_case_insensitive(self):
        rows = ts.merge([r(link=f"magnet:?xt=urn:btih:{HASH_A}"),
                         r(link=f"magnet:?xt=urn:btih:{HASH_A.upper()}&dn=x")])
        self.assertEqual(len(rows), 1)

    def test_different_infohash_kept_apart(self):
        rows = ts.merge([r(link=f"magnet:?xt=urn:btih:{HASH_A}"), r(link=f"magnet:?xt=urn:btih:{HASH_B}")])
        self.assertEqual(len(rows), 2)

    def test_page_links_merge_by_url(self):
        page = "https://www.limetorrents.lol/ubuntu-torrent-1.html"
        rows = ts.merge([r(link=page), r(link=page), r(link=page + "?x")])
        self.assertEqual(len(rows), 2)

    def test_sorted_by_score_with_score_set(self):
        rows = ts.merge([r(seeds=1, link=f"magnet:?xt=urn:btih:{HASH_A}"),
                         r(seeds=9, link=f"magnet:?xt=urn:btih:{HASH_B}")])
        self.assertEqual([x["score"] for x in rows], [9.0, 1.0])

    def test_empty(self):
        self.assertEqual(ts.merge([]), [])


class SizeTest(unittest.TestCase):
    def test_parse_size(self):
        self.assertEqual(ts.parse_size("1.5 GiB"), int(1.5 * 1024 ** 3))
        self.assertEqual(ts.parse_size("700 MB"), 700 * 1024 ** 2)
        self.assertEqual(ts.parse_size("12 B"), 12)
        self.assertEqual(ts.parse_size(""), -1)
        self.assertEqual(ts.parse_size("?"), -1)

    def test_row_size(self):
        self.assertEqual(ts.row("n", "2048", 0, 0, "e", "l")["size"], 2048)
        self.assertEqual(ts.row("n", "-1", 0, 0, "e", "l")["size"], -1)
        self.assertEqual(ts.row("n", "1.5 GB", 0, 0, "e", "l")["size"], -1)

    def test_human(self):
        self.assertEqual(ts.human(-1), "?")
        self.assertEqual(ts.human(1536), "1.5KB")


if __name__ == "__main__":
    unittest.main()
