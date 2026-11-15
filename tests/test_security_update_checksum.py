"""Regression tests for SHA-256 verification of update archives."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from pluto.update import _verify_sha256, download


class UpdateChecksumTests(unittest.TestCase):
    def test_correct_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "release.zip"
            p.write_bytes(b"release archive")
            _verify_sha256(p, hashlib.sha256(p.read_bytes()).hexdigest())

    def test_rejects_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "release.zip"
            p.write_bytes(b"tampered")
            with self.assertRaises(RuntimeError):
                _verify_sha256(p, "0" * 64)

    def test_rejects_malformed_checksum(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "release.zip"
            p.write_bytes(b"data")
            with self.assertRaises(RuntimeError):
                _verify_sha256(p, "not-a-hash")

    def test_missing_checksum_blocks_before_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(RuntimeError):
                download("v99.99.99", Path(tmp))


if __name__ == "__main__":
    unittest.main()
