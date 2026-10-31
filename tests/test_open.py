"""--open N must only ever open result N of the last search."""
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

import torrent_search as ts

ROWS = [ts.row(f"debian-12.{i}.0-amd64-netinst.iso", 1, 1, 0, "piratebay", f"magnet:?xt=urn:btih:{c * 40}")
        for i, c in enumerate("abc")]


class OpenResultTest(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(ROWS, f)
        self.addCleanup(os.remove, self.path)
        for target in (mock.patch.object(ts, "LAST_RESULTS", self.path),
                       mock.patch.object(ts.subprocess, "run")):
            target.start()
            self.addCleanup(target.stop)
        self.opened = []
        if os.name == "nt":
            p = mock.patch.object(ts.os, "startfile", self.opened.append)
            p.start()
            self.addCleanup(p.stop)
        else:
            ts.subprocess.run.side_effect = lambda argv, **kw: self.opened.append(argv[-1])

    def test_opens_requested_result(self):
        with mock.patch("sys.stdout"):
            ts.open_result(2)
        self.assertEqual(self.opened, [ROWS[1]["link"]])

    def test_zero_and_negative_are_refused(self):
        for n in (0, -1, -3):
            with self.subTest(n=n), self.assertRaises(SystemExit):
                ts.open_result(n)
        self.assertEqual(self.opened, [])

    def test_out_of_range_is_refused(self):
        with self.assertRaises(SystemExit):
            ts.open_result(4)
        self.assertEqual(self.opened, [])

    def test_cli_rejects_non_numbers(self):
        for arg in ("abc", "-1", "1; calc", "0x1", "²"):
            with self.subTest(arg=arg), mock.patch.object(sys, "argv", ["ts", "--open", arg]), \
                    self.assertRaises(SystemExit) as cm:
                ts.main()
            self.assertIn("result number", str(cm.exception.code))
        self.assertEqual(self.opened, [])


if __name__ == "__main__":
    unittest.main()
