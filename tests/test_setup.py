"""setup.py keeps going when one download fails and still exits non-zero."""
import contextlib
import hashlib
import io
import os
import tempfile
import unittest
import urllib.error
from unittest import mock

import setup

GOOD = b"# engine\n"


def fake_download(url):
    if "down" in url:
        raise urllib.error.URLError("host unreachable")
    if "timeout" in url:
        raise TimeoutError("timed out")
    return GOOD


class SetupTest(unittest.TestCase):
    def test_failed_download_does_not_stop_the_rest(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        sha = hashlib.sha256(GOOD).hexdigest()
        sources = (("engines/a.py", "https://down.example/a.py", sha),
                   ("engines/b.py", "https://timeout.example/b.py", sha),
                   ("engines/c.py", "https://ok.example/c.py", sha),
                   ("engines/d.py", "https://ok.example/d.py", "0" * 64))
        err = io.StringIO()
        with mock.patch.multiple(setup, NOVA_DIR=tmp.name, ENGINES_DIR=os.path.join(tmp.name, "engines"),
                                 SOURCES=sources, download=fake_download), \
                mock.patch("sys.argv", ["setup.py"]), contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as cm:
            setup.main()
        self.assertEqual(cm.exception.code, 1)
        engines = os.path.join(tmp.name, "engines")
        self.assertTrue(os.path.exists(os.path.join(engines, "c.py")))
        for name in ("a.py", "b.py", "d.py"):
            self.assertFalse(os.path.exists(os.path.join(engines, name)), name)
        self.assertIn("FAILED engines/a.py", err.getvalue())
        self.assertIn("FAILED engines/b.py", err.getvalue())
        self.assertIn("REFUSED engines/d.py", err.getvalue())


if __name__ == "__main__":
    unittest.main()
