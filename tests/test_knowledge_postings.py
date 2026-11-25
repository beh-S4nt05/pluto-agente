"""Regression tests for persisted RAG postings and legacy compatibility."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from pluto import knowledge


class KnowledgeIndexTests(unittest.TestCase):
    def test_rank_and_citations_match_legacy_without_retokenizing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = SimpleNamespace(data_dir=root)
            folder = knowledge.biblioteca_dir(cfg)
            (folder / "a.md").write_text("memória projeto validação", encoding="utf-8")
            (folder / "b.txt").write_text("memória projeto projeto", encoding="utf-8")
            (folder / "c.txt").write_text("outro documento", encoding="utf-8")
            knowledge.indexar(cfg)
            path = folder / "indice.json"
            indexed = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(indexed["postings_version"], 1)
            legacy = dict(indexed)
            legacy.pop("postings_version")
            legacy.pop("postings")
            queries = ["memória", "projeto validação", "ausente", "MEMÓRIA", ""]
            path.write_text(json.dumps(legacy), encoding="utf-8")
            expected = [knowledge.buscar(cfg, q) for q in queries]
            self.assertEqual(expected[0][0]["fonte"], "a.md (trecho #1)")
            path.write_text(json.dumps(indexed), encoding="utf-8")
            with patch.object(knowledge, "_tokens", wraps=knowledge._tokens) as tokenize:
                actual = [knowledge.buscar(cfg, q) for q in queries]
            self.assertEqual(actual, expected)
            self.assertEqual(tokenize.call_count, 4)
            (folder / "a.md").unlink()
            knowledge.indexar(cfg)
            self.assertFalse(any("a.md" in x["fonte"] for x in knowledge.buscar(cfg, "memória")))

    def test_failed_publish_preserves_previous_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = SimpleNamespace(data_dir=Path(tmp))
            folder = knowledge.biblioteca_dir(cfg)
            (folder / "a.txt").write_text("primeiro documento", encoding="utf-8")
            knowledge.indexar(cfg)
            before = (folder / "indice.json").read_bytes()
            (folder / "a.txt").write_text("segundo documento", encoding="utf-8")
            with patch.object(Path, "replace", side_effect=OSError("simulated")):
                with self.assertRaises(OSError):
                    knowledge.indexar(cfg)
            self.assertEqual((folder / "indice.json").read_bytes(), before)
            self.assertEqual(list(folder.glob("*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
