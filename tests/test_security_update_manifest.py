"""Offline tests for a locally trusted update checksum manifest."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pluto.update import _trusted_checksum


class TrustedManifestTests(unittest.TestCase):
    def test_version_specific_hash(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            root = Path(tmp)
            (root / "data").mkdir()
            (root / "data" / "update-checksums.json").write_text(
                json.dumps({"v9.1.0": "a" * 64, "v9.2.0": "b" * 64}))
            self.assertEqual(_trusted_checksum("v9.1.0", root), "a" * 64)
            self.assertIsNone(_trusted_checksum("v9.3.0", root))

    def test_environment_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"PLUTO_UPDATE_SHA256": "c" * 64}):
                self.assertEqual(_trusted_checksum("v9.1.0", Path(tmp)), "c" * 64)

    def test_rejects_malformed_manifest(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            root = Path(tmp)
            (root / "data").mkdir()
            (root / "data" / "update-checksums.json").write_text('{"v9.1.0":"bad"}')
            self.assertIsNone(_trusted_checksum("v9.1.0", root))

    def test_rejects_manifest_symlink(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            root = Path(tmp)
            (root / "data").mkdir()
            real = root / "actual.json"
            real.write_text(json.dumps({"v9.1.0": "a" * 64}))
            try:
                (root / "data" / "update-checksums.json").symlink_to(real)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation unavailable")
            self.assertIsNone(_trusted_checksum("v9.1.0", root))


if __name__ == "__main__":
    unittest.main()
