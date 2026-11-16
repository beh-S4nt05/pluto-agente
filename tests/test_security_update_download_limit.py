"""Offline regression tests for bounded release downloads."""
import io
import tempfile
import unittest
from pathlib import Path

from pluto.update import _copy_bounded


class BoundedUpdateDownloadTests(unittest.TestCase):
    def test_accepts_exact_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "archive.zip"
            _copy_bounded(io.BytesIO(b"12345"), target, limit=5)
            self.assertEqual(target.read_bytes(), b"12345")

    def test_rejects_over_limit_and_removes_partial_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "archive.zip"
            with self.assertRaises(RuntimeError):
                _copy_bounded(io.BytesIO(b"123456"), target, limit=5)
            self.assertFalse(target.exists())

    def test_accepts_empty_download(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "archive.zip"
            _copy_bounded(io.BytesIO(b""), target, limit=5)
            self.assertEqual(target.read_bytes(), b"")

    def test_removes_partial_file_on_read_error(self):
        class BrokenStream:
            def read(self, count):
                raise OSError("network error")

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "archive.zip"
            with self.assertRaises(OSError):
                _copy_bounded(BrokenStream(), target, limit=5)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
