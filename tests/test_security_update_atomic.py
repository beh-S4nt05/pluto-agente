"""Regression tests for atomic per-file update replacement."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pluto.update import _copy_file_atomic, apply_update


class AtomicUpdateTests(unittest.TestCase):
    def test_replaces_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.txt"
            target = root / "dest" / "target.txt"
            source.write_text("new")
            target.parent.mkdir()
            target.write_text("old")
            _copy_file_atomic(source, target)
            self.assertEqual(target.read_text(), "new")
            self.assertFalse(list(target.parent.glob(".pluto-update-*")))

    def test_copy_failure_preserves_old_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.txt"
            target = root / "target.txt"
            source.write_text("new")
            target.write_text("old")
            with patch("pluto.update.shutil.copy2", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    _copy_file_atomic(source, target)
            self.assertEqual(target.read_text(), "old")
            self.assertFalse(list(root.glob(".pluto-update-*")))

    def test_recursive_update_preserves_unrelated_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src, dest = root / "src", root / "dest"
            (src / "pluto").mkdir(parents=True)
            (dest / "pluto").mkdir(parents=True)
            (src / "pluto" / "a.py").write_text("new")
            (dest / "pluto" / "a.py").write_text("old")
            (dest / "pluto" / "local.py").write_text("keep")
            apply_update(src, dest, log=lambda _: None)
            self.assertEqual((dest / "pluto" / "a.py").read_text(), "new")
            self.assertEqual((dest / "pluto" / "local.py").read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
