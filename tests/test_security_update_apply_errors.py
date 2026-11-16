"""Ensure update command reports application errors without false success."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pluto.update import run


class UpdateApplyErrorTests(unittest.TestCase):
    def _run_with_error(self, error):
        messages = []
        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch("pluto.update.latest_tag", return_value="v999.0.0"),
                patch("pluto.update._project_root", return_value=Path(tmp)),
                patch("pluto.update._trusted_checksum", return_value="a" * 64),
                patch("pluto.update.download", return_value=Path(tmp)),
                patch("pluto.update.apply_update", side_effect=error),
                patch("pluto.update.garantir_entry_points") as entry,
            ):
                status = run(assume_yes=True, print_fn=messages.append)
                entry.assert_not_called()
        return status, messages

    def test_runtime_failure_returns_nonzero(self):
        status, messages = self._run_with_error(RuntimeError("rollback incompleto"))
        self.assertEqual(status, 1)
        self.assertTrue(any("rollback incompleto" in m for m in messages))
        self.assertFalse(any("atualização aplicada." in m for m in messages))

    def test_os_failure_returns_nonzero(self):
        status, messages = self._run_with_error(OSError("disco cheio"))
        self.assertEqual(status, 1)
        self.assertTrue(any("disco cheio" in m for m in messages))


if __name__ == "__main__":
    unittest.main()
