"""Regression tests for bounded vault cache and external edits."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from pluto import vault


class VaultCacheTests(unittest.TestCase):
    def test_repeated_search_and_external_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = SimpleNamespace(vault_dir=tmp)
            folder = Path(tmp) / "Pluto" / "memoria"
            folder.mkdir(parents=True)
            note = folder / "nota.md"
            note.write_text("primeiro registro", encoding="utf-8")
            with patch.object(vault, "_read_note", wraps=vault._read_note) as read:
                self.assertEqual(vault.buscar(cfg, "primeiro")["total"], 1)
                self.assertEqual(vault.buscar(cfg, "primeiro")["total"], 1)
                self.assertEqual(read.call_count, 1)
                note.write_text("segundo registro alterado", encoding="utf-8")
                self.assertEqual(vault.buscar(cfg, "primeiro")["total"], 0)
                self.assertEqual(vault.buscar(cfg, "segundo")["total"], 1)
                self.assertEqual(read.call_count, 2)
                note.unlink()
                self.assertEqual(vault.buscar(cfg, "segundo")["total"], 0)

    def test_invalid_utf8_and_symlink_are_not_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = SimpleNamespace(vault_dir=str(root / "vault"))
            folder = Path(cfg.vault_dir) / "Pluto" / "memoria"
            folder.mkdir(parents=True)
            (folder / "bad.md").write_bytes(b"\xff")
            outside = root / "outside.md"
            outside.write_text("externosecreto", encoding="utf-8")
            try:
                (folder / "link.md").symlink_to(outside)
            except (OSError, NotImplementedError):
                pass
            self.assertEqual(vault.buscar(cfg, "externosecreto")["total"], 0)
            self.assertEqual(vault.buscar(cfg, "bad")["total"], 0)
