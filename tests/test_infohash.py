"""Base32 and hex infohashes of the same torrent must merge."""
import base64
import unittest

import torrent_search as ts

HEX = "dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c"  # Big Buck Bunny (WebTorrent sample)
B32 = base64.b32encode(bytes.fromhex(HEX)).decode()


class InfohashTest(unittest.TestCase):
    def test_hex(self):
        self.assertEqual(ts.infohash(f"magnet:?xt=urn:btih:{HEX.upper()}&dn=x"), HEX)

    def test_base32(self):
        self.assertEqual(len(B32), 32)
        self.assertEqual(ts.infohash(f"magnet:?xt=urn:btih:{B32}"), HEX)
        self.assertEqual(ts.infohash(f"magnet:?xt=urn:btih:{B32.lower()}"), HEX)

    def test_invalid_base32_falls_back(self):
        bad = "1" * 32  # '1' is not in the base32 alphabet
        self.assertEqual(ts.infohash(f"magnet:?xt=urn:btih:{bad}"), bad)

    def test_not_a_magnet(self):
        self.assertEqual(ts.infohash("https://archive.org/download/x/x_archive.torrent"), "")

    def test_merge_base32_with_hex(self):
        rows = [ts.row("Big Buck Bunny", 1, 3, 0, "nyaa", f"magnet:?xt=urn:btih:{B32}"),
                ts.row("Big Buck Bunny", 1, 9, 0, "piratebay", f"magnet:?xt=urn:btih:{HEX}")]
        merged = ts.merge(rows)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["engine"], "piratebay")


if __name__ == "__main__":
    unittest.main()
