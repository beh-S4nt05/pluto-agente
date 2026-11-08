"""V9.0.0 (P1 · T243–T244): CONTEXTO DURÁVEL — autonomia sem perder
contexto (macro-fluxo, estágio [4]).

Três peças (o que faltava na auditoria v8.6.0):

1. **Checkpoint por tarefa** — ``<data>/tasks/state/<id>.json``
   (objetivo, critérios de aceitação EXTRAÍDOS do pedido, plano,
   feitos, próximos, bloqueios, última tool, versão). Escrita atômica
   (tmp + replace): crash no meio não corrompe. A tarefa sobrevive a
   compactação, restart e truncamento — ``retomar()`` reconstrói o
   estado sem reler o chat todo ("continua a tarefa X").
2. **Alerta de truncamento** — quando o Agent compacta o contexto, a
   compactação é REGISTRADA no agent.log (fim da perda silenciosa: o
   operador e o diário sabem quantas vezes a janela cortou).
3. **Diário de trabalho** — 1 linha por evento/tarefa concluída em
   ``<data>/diario.jsonl`` (o quê · quando · task · fonte) — memória
   consultável de médio prazo (a P4 usa para o briefing diário).
   Com vault Obsidian configurado, o dia é espelhado como nota
   (escopo ``diario``).

Nada sai da máquina: tudo em data_dir (local-first, D2).
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

_CAMPOS_STR = ("objetivo", "plano", "proximos", "bloqueios")


def _state_dir(cfg) -> Path:
    d = Path(cfg.data_dir) / "tasks" / "state"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _path(cfg, task_id: str) -> Path:
    return _state_dir(cfg) / f"{task_id}.json"


def _novo_id(cfg) -> str:
    """S0001, S0002… (S de sessão — não colide com as T000x do
    orquestrador; o agente pode passar a id que quiser ao salvar)."""
    usado = {p.stem for p in _state_dir(cfg).glob("*.json")}
    n = 1
    while f"S{n:04d}" in usado:
        n += 1
    return f"S{n:04d}"


def _atomic_write(path: Path, texto: str) -> None:
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(texto, encoding="utf-8")
    os.replace(tmp, path)


def salvar(cfg, task_id: str = "", objetivo: str = "", nota: str = "",
           plano: str = "", proximos: str = "", bloqueios: str = "",
           ultima_tool: dict | None = None) -> dict:
    """Cria/atualiza (merge) o checkpoint da tarefa — nunca perde o
    que já estava: campos vazios não sobrescrevem; ``nota`` ANEXA aos
    feitos; ``objetivo`` novo extrai critérios de aceitação."""
    task_id = str(task_id or "").strip() or _novo_id(cfg)
    if not re.fullmatch(r"[\w-]{1,40}", task_id):
        return {"erro": f"id inválida: {task_id!r} (use letras/números)"}
    path = _path(cfg, task_id)
    reg: dict = {}
    if path.is_file():
        try:
            reg = json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # checkpoint corrompido: recomeça honesto
            reg = {}
    novo = not reg
    if novo:
        reg = {"id": task_id, "status": "ativa", "criado":
               time.strftime("%Y-%m-%d %H:%M:%S"), "feitos": [],
               "criterios": [], "versao": 0, "truncamentos": 0}
    for campo in _CAMPOS_STR:
        valor = str(locals()[campo] or "").strip()
        if valor:
            reg[campo] = valor
    if novo or not reg.get("criterios"):
        from .autoavaliacao import extrair_criterios
        reg["criterios"] = extrair_criterios(
            str(reg.get("objetivo") or objetivo or ""))
    nota = str(nota or "").strip()
    if nota:
        reg["feitos"] = (reg.get("feitos") or [])[-49:] + [
            f"[{time.strftime('%H:%M:%S')}] {nota[:300]}"]
    if isinstance(ultima_tool, dict) and ultima_tool:
        reg["ultima_tool"] = {"nome": str(ultima_tool.get("nome", ""))[:60],
                              "ts": time.strftime("%H:%M:%S")}
    reg["versao"] = int(reg.get("versao", 0)) + 1
    reg["atualizado"] = time.strftime("%Y-%m-%d %H:%M:%S")
    reg["ts"] = time.time()     # µs: desempata "mais recente" DENTRO do
    #                            mesmo segundo (ordem de filesystem não
    #                            decide — bug pego pelo CI, run 42503471387)
    _atomic_write(path, json.dumps(reg, ensure_ascii=False, indent=1))
    return reg


def carregar(cfg, task_id: str) -> dict | None:
    """Checkpoint da tarefa (None se não existe/ilegível — honesto)."""
    path = _path(cfg, str(task_id or "").strip())
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def listar(cfg, so_ativas: bool = True) -> list[dict]:
    """Checkpoints (mais recentemente atualizados primeiro)."""
    regs = []
    for p in _state_dir(cfg).glob("*.json"):
        try:
            r = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(r, dict) and r.get("id"):
                regs.append(r)
        except Exception:  # noqa: BLE001
            continue
    if so_ativas:
        regs = [r for r in regs if r.get("status") == "ativa"]
    # recência por ts (µs) com fallback para registros antigos sem ts —
    # empate de segundo NÃO cai na ordem do filesystem (determinístico)
    return sorted(regs, key=lambda r: (float(r.get("ts") or 0),
                                       str(r.get("atualizado", ""))),
                  reverse=True)


def fechar(cfg, task_id: str, resultado: str = "",
           status: str = "concluida") -> dict:
    """Encerra a tarefa e escreve a linha no DIÁRIO (1 linha por
    tarefa concluída — o quê/quando/fonte)."""
    reg = carregar(cfg, task_id)
    if not reg:
        return {"erro": f"checkpoint não encontrado: {task_id!r}"}
    reg["status"] = status if status in ("concluida", "abortada") else \
        "concluida"
    reg["resultado"] = str(resultado or "").strip()[:500]
    reg["atualizado"] = time.strftime("%Y-%m-%d %H:%M:%S")
    reg["ts"] = time.time()
    _atomic_write(_path(cfg, reg["id"]),
                  json.dumps(reg, ensure_ascii=False, indent=1))
    diar(cfg, reg["resultado"] or str(reg.get("objetivo", ""))[:120],
         task_id=reg["id"], fonte="checkpoint")
    return reg


def retomar(cfg, task_id: str = "") -> dict:
    """Estado de continuação — reconstrói a tarefa sem reler o chat.

    Sem id: a tarefa ATIVA mais recentemente atualizada."""
    reg = (carregar(cfg, task_id) if str(task_id or "").strip()
           else (listar(cfg) or [None])[0])
    if not reg:
        return {"erro": "nenhuma tarefa ativa com checkpoint — "
                        "comece com acao=salvar (id opcional)"}
    linhas = [f"RETOMADA DA TAREFA {reg['id']} (versão {reg.get('versao')}, "
              f"iniciada {reg.get('criado')})"]
    if reg.get("objetivo"):
        linhas.append(f"OBJETIVO: {reg['objetivo']}")
    if reg.get("criterios"):
        linhas.append("CRITÉRIOS DE ACEITAÇÃO:")
        linhas += [f"  - {c}" for c in reg["criterios"]]
    if reg.get("plano"):
        linhas.append(f"PLANO: {reg['plano']}")
    if reg.get("feitos"):
        linhas.append("JÁ FEITO (não repita):")
        linhas += [f"  - {f}" for f in reg["feitos"][-8:]]
    if reg.get("proximos"):
        linhas.append(f"PRÓXIMOS PASSOS: {reg['proximos']}")
    if reg.get("bloqueios"):
        linhas.append(f"BLOQUEIOS: {reg['bloqueios']}")
    if reg.get("ultima_tool"):
        linhas.append(f"ÚLTIMA FERRAMENTA: {reg['ultima_tool'].get('nome')}")
    linhas.append("Continue EXATAMENTE de onde parou.")
    return {"ok": True, "tarefa": reg, "prompt": "\n".join(linhas)}


# ─────────────────────────────────────────── alerta de truncamento
def registrar_truncamento(cfg, n_msgs: int) -> None:
    """A compactação de contexto deixou de ser silenciosa: 1 linha no
    agent.log (auditável — quantas vezes a janela cortou na sessão)."""
    try:
        from . import activity
        activity.log(cfg, "contexto",
                     f"🧠 compactação: {int(n_msgs)} mensagens viraram "
                     "resumo — tarefa original e recentes preservados "
                     "(essencial também no checkpoint/diário)")
    except Exception:  # noqa: BLE001
        pass


# ─────────────────────────────────────────────────── diário de trabalho
def _diario_path(cfg) -> Path:
    return Path(cfg.data_dir) / "diario.jsonl"


def diar(cfg, o_que: str, task_id: str = "", fonte: str = "") -> dict:
    """1 linha no diário de trabalho (jsonl local; espelho no vault
    Obsidian quando configurado)."""
    entrada = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
               "o_que": str(o_que or "").strip()[:300],
               "task_id": str(task_id or ""), "fonte": str(fonte or "")}
    if not entrada["o_que"]:
        return {"erro": "diário precisa de 'o_que'"}
    try:
        with _diario_path(cfg).open("a", encoding="utf-8") as f:
            f.write(json.dumps(entrada, ensure_ascii=False) + "\n")
    except OSError as exc:
        return {"erro": f"não consegui escrever no diário: {exc}"}
    _espelhar_vault(cfg, entrada["ts"][:10])
    return {"ok": True, **entrada}


def diario_ler(cfg, dia: str = "", limite: int = 200) -> list[dict]:
    """Linhas do diário (mais recentes por último); ``dia`` filtra
    AAAA-MM-DD (a P4 usa para o briefing da manhã)."""
    path = _diario_path(cfg)
    if not path.is_file():
        return []
    saida = []
    try:
        for linha in path.read_text(encoding="utf-8").splitlines():
            if not linha.strip():
                continue
            try:
                e = json.loads(linha)
            except ValueError:
                continue
            if dia and not str(e.get("ts", "")).startswith(dia):
                continue
            saida.append(e)
    except OSError:
        return []
    return saida[-limite:]


def _espelhar_vault(cfg, dia: str) -> None:
    """Dia inteiro do diário como nota Obsidian (escopo diario) —
    só quando o vault está configurado; falha aqui NUNCA derruba."""
    try:
        from . import vault
        if not vault.ativo(cfg):
            return
        linhas = diario_ler(cfg, dia=dia, limite=100)
        if not linhas:
            return
        corpo = "\n".join(
            f"- {e['ts'][11:16]} · {e['o_que']}"
            + (f" · [{e['task_id']}]" if e.get("task_id") else "")
            for e in linhas)
        vault.salvar(cfg, "diario", f"Diário {dia}", corpo,
                     tags="pluto,diario")
    except Exception:  # noqa: BLE001
        pass
