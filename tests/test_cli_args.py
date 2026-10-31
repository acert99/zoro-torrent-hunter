"""Command-line argument errors end with a usage message, not a traceback."""
import contextlib
import io
import sys
import unittest
from unittest import mock

import torrent_search as ts


class EnginesArgTest(unittest.TestCase):
    def test_empty_engine_list(self):
        for value in ("", " , ,"):
            err = io.StringIO()
            with self.subTest(value=value), mock.patch.object(sys, "argv", ["ts", "ubuntu", "--engines", value]), \
                    contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as cm:
                ts.main()
            self.assertEqual(cm.exception.code, 2)
            self.assertIn("at least one engine", err.getvalue())


if __name__ == "__main__":
    unittest.main()
