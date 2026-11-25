"""Memory ranking must use a single snapshot and normalize the query once."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from pluto.memory import MemoryStore


class MemorySnapshotTests(unittest.TestCase):
    def test_prompt_uses_one_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = MemoryStore(SimpleNamespace(data_dir=Path(tmp), memory_top_k=2))
            store.add("projeto " + "a" * 800)
            store.add("agenda " + "b" * 800)
            store.add("memória " + "c" * 800)
            with patch.object(store, "list_all", wraps=store.list_all) as read:
                prompt = store.prompt_section("projeto")
            self.assertEqual(read.call_count, 1)
            self.assertIn("projeto", prompt)

    def test_ranking_preserves_accent_and_recent_facts(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = MemoryStore(SimpleNamespace(data_dir=Path(tmp)))
            first = store.add("validação técnica")
            store.add("agenda")
            store.add("finanças")
            result = store.relevant("validacao tecnica", k=1)
            self.assertEqual(result[0]["id"], first["id"])
            self.assertEqual(len(result), 3)
