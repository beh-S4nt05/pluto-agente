"""Update must not follow pre-existing filesystem symlinks."""
import tempfile
import unittest
from pathlib import Path

from pluto.update import apply_update


class UpdateDestinationSymlinkTests(unittest.TestCase):
    def test_rejects_nested_destination_symlink_without_partial_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src, dst, outside = root / "src", root / "dst", root / "outside"
            (src / "pluto" / "config").mkdir(parents=True)
            (src / "pluto" / "config" / "settings.py").write_text("safe")
            (dst / "pluto").mkdir(parents=True)
            outside.mkdir()
            try:
                (dst / "pluto" / "config").symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation not available on this runner")
            with self.assertRaises(RuntimeError):
                apply_update(src, dst, log=lambda _: None)
            self.assertFalse((outside / "settings.py").exists())

    def test_rejects_source_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src, dst, outside = root / "src", root / "dst", root / "outside.txt"
            src.mkdir()
            dst.mkdir()
            outside.write_text("secret")
            try:
                (src / "linked.txt").symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation not available on this runner")
            with self.assertRaises(RuntimeError):
                apply_update(src, dst, log=lambda _: None)
            self.assertFalse((dst / "linked.txt").exists())

    def test_regular_update_still_copies(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src, dst = root / "src", root / "dst"
            (src / "pluto").mkdir(parents=True)
            dst.mkdir()
            (src / "pluto" / "ok.py").write_text("ok")
            self.assertEqual(apply_update(src, dst, log=lambda _: None), ["pluto"])
            self.assertEqual((dst / "pluto" / "ok.py").read_text(), "ok")


if __name__ == "__main__":
    unittest.main()
