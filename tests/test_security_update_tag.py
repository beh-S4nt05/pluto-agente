"""Reject malformed release tags before any network request or file write."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pluto.update import download


class UpdateTagValidationTests(unittest.TestCase):
    def test_rejects_unsafe_tags_before_network(self):
        for tag in ("../escape", "v1.2.3/../../oops", "v1.2.3?x=1",
                    "v1.2.3#fragment", "v1.2.3-rc1", "v1.2.3\\evil",
                    "https://evil.example/", "", "v1.2.3%2Fbad"):
            with self.subTest(tag=tag), tempfile.TemporaryDirectory() as tmp:
                with patch("pluto.update.urllib.request.urlopen") as urlopen:
                    with self.assertRaises(RuntimeError):
                        download(tag, Path(tmp), "a" * 64)
                    urlopen.assert_not_called()
                self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_rejects_invalid_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(RuntimeError):
                download(None, Path(tmp), "a" * 64)

    def test_valid_tag_reaches_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("pluto.update.urllib.request.urlopen", side_effect=OSError("offline")) as urlopen:
                with self.assertRaises(OSError):
                    download("v9.1.0", Path(tmp), "a" * 64)
                urlopen.assert_called_once()


if __name__ == "__main__":
    unittest.main()
