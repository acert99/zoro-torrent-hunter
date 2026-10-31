"""rutor and yts links: direct .torrent downloads and infohash URLs need no magnet resolution."""
import io
import json
import os
import tempfile
import unittest
from unittest import mock

import torrent_search as ts

NOTLD = "50B7DAFB7137CBECF045F78E8EFBE4AC1A90D139"  # Night of the Living Dead (1968), public domain


def nova_output(*links):
    name = "Night%20of%20the%20Living%20Dead%20%281968%29"
    return "".join(f"{link}|{name}|785000000|12|3|https://example/|https://example/desc\n" for link in links)


class FakeProc:
    def __init__(self, out):
        self.out = out

    def communicate(self, timeout=None):
        return self.out, None


class SearchNovaTest(unittest.TestCase):
    def search(self, engine, out):
        with mock.patch.object(ts.subprocess, "Popen", return_value=FakeProc(out)):
            return ts.search_nova(engine, "night of the living dead", "all")

    def test_yts_download_url_becomes_magnet(self):
        rows = self.search("yts", nova_output(f"https://yts.gg/torrent/download/{NOTLD}"))
        link = rows[0]["link"]
        self.assertTrue(link.startswith(f"magnet:?xt=urn:btih:{NOTLD.lower()}&dn=Night+of+the+Living+Dead"))
        self.assertTrue(ts.MAGNET_RE.fullmatch(link))
        self.assertEqual(rows[0]["infohash"], NOTLD.lower())
        self.assertEqual(rows[0]["name"], "Night of the Living Dead (1968)")

    def test_other_yts_domains(self):
        rows = self.search("yts", nova_output(f"https://yts.bz/torrent/download/{NOTLD}"))
        self.assertTrue(rows[0]["link"].startswith("magnet:"))

    def test_only_yts_is_rewritten(self):
        url = f"https://yts.gg/torrent/download/{NOTLD}"
        self.assertEqual(self.search("limetorrents", nova_output(url))[0]["link"], url)

    def test_unexpected_yts_link_kept(self):
        url = "https://yts.gg/movies/night-of-the-living-dead-1968"
        self.assertEqual(self.search("yts", nova_output(url))[0]["link"], url)


class TorrentUrlTest(unittest.TestCase):
    def test_direct_links(self):
        for engine, link in (("rutor", "https://d.rutor.info/download/1099896"),
                             ("archive", "https://archive.org/download/night_of_the_living_dead/night_of_the_living_dead_archive.torrent"),
                             ("academictorrents", f"https://academictorrents.com/download/{NOTLD.lower()}.torrent")):
            with self.subTest(engine=engine):
                self.assertTrue(ts.is_torrent_url(engine, link))

    def test_refused(self):
        for engine, link in (("rutor", "https://rutor.info/torrent/1099896/ubuntu"),
                             ("rutor", "https://d.rutor.info.evil.example/download/1"),
                             ("rutor", "http://d.rutor.info/download/1"),
                             ("limetorrents", "https://d.rutor.info/download/1"),
                             ("archive", "https://archive.org/download/a/b_archive.torrent?x=1"),
                             ("archive", "https://archive.org.evil.example/download/a/a_archive.torrent")):
            with self.subTest(engine=engine, link=link):
                self.assertFalse(ts.is_torrent_url(engine, link))


class RowFlagTest(unittest.TestCase):
    def test_row_marks_direct_downloads(self):
        self.assertTrue(ts.row("x", 1, 1, 0, "rutor", "https://d.rutor.info/download/1")["torrent"])
        self.assertFalse(ts.row("x", 1, 1, 0, "limetorrents", "https://d.rutor.info/download/1")["torrent"])
        self.assertFalse(ts.row("x", 1, 1, 0, "rutor", f"magnet:?xt=urn:btih:{NOTLD}")["torrent"])


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


class FetchTorrentTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        p = mock.patch.object(ts, "LAST_RESULTS", os.path.join(tmp.name, "not-created-yet", "last.json"))
        p.start()
        self.addCleanup(p.stop)

    def fetch(self, body):
        with mock.patch.object(ts.urllib.request, "urlopen", return_value=FakeResponse(body)):
            return ts.fetch_torrent("https://d.rutor.info/download/1")

    def test_saves_torrent(self):
        path = self.fetch(b"d8:announce3:urle")
        self.assertTrue(path.endswith(".torrent"))
        with open(path, "rb") as f:
            self.assertEqual(f.read(), b"d8:announce3:urle")

    def test_refuses_non_torrent(self):
        self.assertEqual(self.fetch(b"<html>blocked</html>"), "")

    def test_refuses_huge_file(self):
        self.assertEqual(self.fetch(b"d" + b"0" * ts.MAX_TORRENT), "")


class OpenDirectTest(unittest.TestCase):
    def test_rutor_download_opens_in_torrent_client(self):
        link = "https://d.rutor.info/download/1099896"
        rows = [ts.row("Ubuntu 24.04.1", 1, 1, 0, "rutor", link)]
        opened = []
        with mock.patch.object(ts.json, "load", return_value=rows), mock.patch("builtins.open", mock.mock_open()),                 mock.patch.object(ts, "resolve_magnet", side_effect=AssertionError("must not resolve")),                 mock.patch.object(ts, "fetch_torrent", return_value="/cache/x.torrent") as fetch,                 mock.patch.object(ts.subprocess, "run", side_effect=lambda argv, **kw: opened.append(argv[-1])),                 mock.patch.object(ts.os, "startfile", opened.append, create=True), mock.patch("sys.stdout"):
            ts.open_result(1)
        fetch.assert_called_once_with(link)
        self.assertEqual(opened, ["/cache/x.torrent"])

    def test_failed_download_is_not_opened(self):
        rows = [ts.row("Ubuntu", 1, 1, 0, "rutor", "https://d.rutor.info/download/1")]
        with mock.patch.object(ts.json, "load", return_value=rows), mock.patch("builtins.open", mock.mock_open()),                 mock.patch.object(ts, "fetch_torrent", side_effect=OSError("down")),                 mock.patch.object(ts.subprocess, "run") as run,                 mock.patch.object(ts.os, "startfile", create=True) as startfile, self.assertRaises(SystemExit):
            ts.open_result(1)
        run.assert_not_called()
        startfile.assert_not_called()


class RutorConfigTest(unittest.TestCase):
    def test_setup_turns_on_rutor_magnets(self):
        import setup
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        with mock.patch.multiple(setup, NOVA_DIR=tmp.name, ENGINES_DIR=os.path.join(tmp.name, "engines"), SOURCES=()),                 mock.patch("sys.argv", ["setup.py"]), self.assertRaises(SystemExit) as cm:
            setup.main()
        self.assertEqual(cm.exception.code, 0)
        with open(os.path.join(tmp.name, "engines", "rutor.json"), encoding="utf-8") as f:
            cfg = json.load(f)
        self.assertIs(cfg["magnet"], True)
        self.assertEqual(set(cfg), {"magnet", "proxy", "proxies", "ua"})  # the plugin resets the file otherwise


if __name__ == "__main__":
    unittest.main()
