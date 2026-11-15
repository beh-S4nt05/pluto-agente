"""Regression tests for unsafe release archives (offline)."""
import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from pluto.update import _assert_zip_seguro


class UpdateArchiveSecurityTests(unittest.TestCase):
    def _check(self, entries):
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w") as zf:
            for name, content, mode in entries:
                info = zipfile.ZipInfo(name)
                if mode is not None:
                    info.create_system = 3
                    info.external_attr = mode << 16
                zf.writestr(info, content)
        data.seek(0)
        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(data) as zf:
                _assert_zip_seguro(zf, Path(tmp))

    def test_normal_archive(self):
        self._check([("pluto-release/pluto/main.py", "ok", None)])

    def test_rejects_path_traversal(self):
        with self.assertRaises(RuntimeError):
            self._check([("../escape", "bad", None)])

    def test_rejects_symlink(self):
        with self.assertRaises(RuntimeError):
            self._check([("pluto-release/link", "../outside", 0o120777)])

    def test_rejects_duplicate_entries(self):
        with self.assertWarns(UserWarning):
            with self.assertRaises(RuntimeError):
                self._check([("same.txt", "one", None), ("same.txt", "two", None)])

    def test_rejects_large_declared_file(self):
        info = zipfile.ZipInfo("huge.bin")
        info.file_size = 101 * 1024 * 1024
        with tempfile.TemporaryDirectory() as tmp:
            class FakeArchive:
                def infolist(self):
                    return [info]
            with self.assertRaises(RuntimeError):
                _assert_zip_seguro(FakeArchive(), Path(tmp))


if __name__ == "__main__":
    unittest.main()
