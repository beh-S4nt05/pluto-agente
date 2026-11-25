"""Baseline local, sintético e sem LLM dos caminhos reais de conhecimento.
Executar na raiz: python -m benchmarks.baseline --files 1000 --repeat 5
Não lê dados pessoais; todas as fixtures e índices vivem em TemporaryDirectory.
"""
from __future__ import annotations

import argparse
import json
import math
import platform
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace

from pluto import grafo, knowledge, vault


def measure(fn, repeat):
    samples = []
    result = None
    for _ in range(repeat):
        start = perf_counter()
        result = fn()
        samples.append((perf_counter() - start) * 1000)
    ordered = sorted(samples)
    return {
        "median_ms": round(statistics.median(samples), 3),
        "p95_ms": round(ordered[math.ceil(.95 * len(ordered)) - 1], 3),
        "samples_ms": [round(x, 3) for x in samples],
    }, result


def require(condition, label):
    if not condition:
        raise RuntimeError("Falha de verificação: " + label)


def run(files, repeat):
    with tempfile.TemporaryDirectory(prefix="pluto-bench-") as tmp:
        root = Path(tmp)
        cfg = SimpleNamespace(data_dir=root / "data", vault_dir=str(root / "vault"))
        cfg.data_dir.mkdir()
        corpus = root / "corpus"
        notes = Path(cfg.vault_dir) / "Pluto" / "memoria"
        sources = root / "sources"
        for folder in (corpus, notes, sources):
            folder.mkdir(parents=True)
        for i in range(files):
            marker = "marcadorfinal" if i == files - 1 else "conteudocomum"
            body = (f"Documento {i}: memória, projeto, validação e {marker}.\n" * 25)
            (corpus / f"doc{i:07d}.txt").write_text(body, encoding="utf-8")
            (notes / f"nota{i:07d}.md").write_text(body, encoding="utf-8")
            (sources / f"mod{i:07d}.py").write_text(
                f"def func{i}():\n    return helper()\n\ndef helper():\n    return {i}\n",
                encoding="utf-8")
        timings = {}
        timings["rag_index"], index = measure(lambda: knowledge.indexar(cfg, corpus), repeat)
        require(index["livros"] == files and index["blocos"] >= files, "rag index")
        timings["rag_hit"], hits = measure(lambda: knowledge.buscar(cfg, "marcadorfinal", pasta=corpus), repeat)
        require(bool(hits) and f"doc{files-1:07d}.txt" in hits[0]["fonte"], "rag hit")
        timings["rag_miss"], misses = measure(lambda: knowledge.buscar(cfg, "termoausentexyz", pasta=corpus), repeat)
        require(not misses, "rag miss")
        timings["vault_hit"], hits = measure(lambda: vault.buscar(cfg, "marcadorfinal"), repeat)
        require(hits["total"] == 1 and hits["achados"][0]["nota"] == f"nota{files-1:07d}", "vault hit")
        timings["vault_miss"], misses = measure(lambda: vault.buscar(cfg, "termoausentexyz"), repeat)
        require(misses["total"] == 0, "vault miss")
        timings["graph_build"], graph = measure(lambda: grafo.build(cfg, sources), repeat)
        require(graph["arquivos"] == files and graph["simbolos"] == files * 2 and not graph["avisos"], "graph build")
        timings["graph_query"], hits = measure(lambda: grafo.query(cfg, f"mod{files-1:07d}.func{files-1}"), repeat)
        require(hits["ok"] and len(hits["simbolos"]) == 1, "graph query")
        return timings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--files", type=int, default=1000)
    parser.add_argument("--repeat", type=int, default=5)
    args = parser.parse_args()
    if not 1 <= args.files <= 100000 or not 1 <= args.repeat <= 100:
        parser.error("files: 1..100000; repeat: 1..100")
    try:
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        sha = None
    print(json.dumps({
        "sha": sha, "python": sys.version, "platform": platform.platform(),
        "files": args.files, "repeat": args.repeat,
        "cache_conditions": "filesystem cache uncontrolled; repeated warm/mixed runs",
        "timings": run(args.files, args.repeat),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
