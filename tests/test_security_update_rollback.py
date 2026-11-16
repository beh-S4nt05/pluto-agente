"""Offline tests for rollback of partially applied updates."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pluto.update import apply_update, _copy_file_atomic


class UpdateRollbackTests(unittest.TestCase):
    def test_restores_existing_files_after_later_copy_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src, dest = root / "src", root / "dest"
            src.mkdir()
            dest.mkdir()
            (src / "a.txt").write_text("new a")
            (src / "b.txt").write_text("new b")
            (dest / "a.txt").write_text("old a")
            (dest / "b.txt").write_text("old b")
            calls = 0
            def fail_second(source, target):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("simulated disk failure")
                return _copy_file_atomic(source, target)
            with patch("pluto.update._copy_file_atomic", side_effect=fail_second):
                with self.assertRaises(OSError):
                    apply_update(src, dest, log=lambda _: None)
            self.assertEqual((dest / "a.txt").read_text(), "old a")
            self.assertEqual((dest / "b.txt").read_text(), "old b")

    def test_removes_new_files_after_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src, dest = root / "src", root / "dest"
            src.mkdir()
            dest.mkdir()
            (src / "a.txt").write_text("new a")
            (src / "b.txt").write_text("new b")
            calls = 0
            def fail_second(source, target):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("simulated disk failure")
                return _copy_file_atomic(source, target)
            with patch("pluto.update._copy_file_atomic", side_effect=fail_second):
                with self.assertRaises(OSError):
                    apply_update(src, dest, log=lambda _: None)
            self.assertFalse((dest / "a.txt").exists())
            self.assertFalse((dest / "b.txt").exists())

    def test_successful_update(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src, dest = root / "src", root / "dest"
            src.mkdir()
            dest.mkdir()
            (src / "a.txt").write_text("new")
            (dest / "a.txt").write_text("old")
            self.assertEqual(apply_update(src, dest, log=lambda _: None), ["a.txt"])
            self.assertEqual((dest / "a.txt").read_text(), "new")


if __name__ == "__main__":
    unittest.main()
