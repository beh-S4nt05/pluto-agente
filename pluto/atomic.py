# -*- coding: utf-8 -*-
"""✍️ Escrita atômica — helper ÚNICO (V9.0.0 · P8.2 · T259).

Auditoria SDD (M6): "NFR-03 diz atômica em tudo que persiste", mas o
codebase tinha ~53 `write_text` diretos — crash no meio deixava arquivo
pela metade (config.yaml, current.json, secretario.json, lembretes.json,
notifications.json). Regra da casa (contexto.py desde a P1) promovida a
módulo: **tmp + ``os.replace``** (atômico no POSIX e no Windows NTFS) —
crash no meio nunca corrompe; sobra no máximo um ``.tmp`` ignorável.
"""
from __future__ import annotations

import itertools
import os
import threading
import time
from pathlib import Path

_SEQ = itertools.count()      # contador thread-safe p/ tmp único


def atomic_write(path: Path | str, texto: str) -> None:
    """Grava ``texto`` em ``path`` de forma atômica (tmp + replace).

    Cria diretórios pais se faltarem. Levanta OSError da escrita real —
    quem chama decide se engole (e deve LOGAR, nunca silêncio).

    CONCORRÊNCIA (lições do T71 na P8.2 — ele pegou as duas):
    - o tmp é ÚNICO POR ESCRITA (pid · thread · sequência) — escritas
      paralelas não disputam o mesmo tmp (a primeira dava replace e a
      segunda explodia FileNotFoundError);
    - no WINDOWS, ``os.replace`` falha com PermissionError se o destino
      estiver aberto por um LEITOR (WinError 5). Retry curto; se a
      contenção persistir, cai para escrita direta de último-vencedor
      (o comportamento pré-atômico) — nunca derruba quem chama.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(f"{p.name}.{os.getpid()}.{threading.get_ident()}"
                      f".{next(_SEQ)}.tmp")
    tmp.write_text(texto, encoding="utf-8")
    try:
        for tentativa in range(4):
            try:
                os.replace(tmp, p)
                return
            except PermissionError:    # Win: destino aberto por leitor
                time.sleep(0.005 * (tentativa + 1))
        p.write_text(texto, encoding="utf-8")   # último-vencedor
    finally:
        tmp.unlink(missing_ok=True)
