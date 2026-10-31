"""build.py ships only the files setup.py wrote into vendor/, never runtime leftovers."""
import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

import build
import setup


class VendorFilesTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = tmp.name
        p = mock.patch.object(build, "HERE", self.root)
        p.start()
        self.addCleanup(p.stop)

    def touch(self, rel):
        path = os.path.join(self.root, "vendor", "nova3", *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w").close()

    def test_only_setup_files(self):
        for f in setup.vendor_files():
            self.touch(f)
        for leftover in ("engines/rutor.log", "engines/rutor.ico", "engines/__pycache__/rutor.cpython-312.pyc",
                         "engines/other.json", "notes.txt"):
            self.touch(leftover)
        shipped = {os.path.relpath(f, os.path.join("vendor", "nova3")).replace(os.sep, "/") for f in build.vendor_files()}
        self.assertEqual(shipped, set(setup.vendor_files()))
        self.assertIn("engines/rutor.json", shipped)
        self.assertIn("engines/__init__.py", shipped)
        self.assertIn("nova2dl.py", shipped)

    def test_missing_file_stops_the_build(self):
        for f in setup.vendor_files()[1:]:
            self.touch(f)
        with self.assertRaises(SystemExit) as cm:
            build.vendor_files()
        self.assertIn(setup.vendor_files()[0], str(cm.exception.code).replace(os.sep, "/"))

    def test_stdlib_imports_read_only_shipped_plugins(self):
        for f in setup.vendor_files():
            self.touch(f)
        path = os.path.join(self.root, "vendor", "nova3", "engines", "yts.py")
        with open(path, "w") as f:
            f.write("import sqlite3\n")
        with open(os.path.join(self.root, "vendor", "nova3", "engines", "stray.py"), "w") as f:
            f.write("import tkinter\n")
        mods = build.plugin_stdlib_imports()
        self.assertIn("sqlite3", mods)
        self.assertNotIn("tkinter", mods)


if __name__ == "__main__":
    unittest.main()
