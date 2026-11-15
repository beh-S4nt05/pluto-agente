"""Regressões de privacidade para logs persistentes de auditoria."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from pluto import audit


class AuditRedactionTests(unittest.TestCase):
    def test_nested_credentials_are_redacted(self):
        args = {"token": "top-secret", "nested": {"api_key": "private",
                "headers": {"Authorization": "Bearer hidden"}},
                "items": [{"password": "pass123"}], "path": "notes.txt"}
        cleaned = audit._chop(args)
        serialized = json.dumps(cleaned)
        for secret in ("top-secret", "private", "Bearer hidden", "pass123"):
            self.assertNotIn(secret, serialized)
        self.assertEqual(cleaned["path"], "notes.txt")
        self.assertEqual(cleaned["nested"]["api_key"], "[REDACTED]")

    def test_audit_does_not_persist_tool_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = SimpleNamespace(data_dir=Path(tmp))
            audit.log(cfg, "pluto", "read_file", {"path": "notes.txt"},
                      True, output="confidential file contents")
            files = list((Path(tmp) / "audit").glob("*.jsonl"))
            self.assertEqual(len(files), 1)
            saved = files[0].read_text(encoding="utf-8")
            self.assertNotIn("confidential file contents", saved)
            self.assertIn("OMITTED", saved)

    def test_persisted_secret_args_are_redacted(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = SimpleNamespace(data_dir=Path(tmp))
            audit.log(cfg, "pluto", "mcp_call",
                      {"auth_token": "sensitive123",
                       "payload": {"client_secret": "secret456"}},
                      False, output="secret789")
            saved = next((Path(tmp) / "audit").glob("*.jsonl")).read_text()
            for secret in ("sensitive123", "secret456", "secret789"):
                self.assertNotIn(secret, saved)
            self.assertIn("[REDACTED]", saved)


if __name__ == "__main__":
    unittest.main()
