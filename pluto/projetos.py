# -*- coding: utf-8 -*-
"""📁 Projetos como NODES — V9.0.0 (P8 · T253).

Proposta do operador (09/11/2026): organizar o trabalho em PROJETOS —
cada projeto é um node que mantém JUNTOS o que hoje vive espalhado:

    Projeto → RPG
    ├── Conversas           (as sessões daquele projeto)
    ├── Contextos etc       (contexto.md + anotações datadas)
    └── Recursos/artefatos  (o que o agente GERA para o projeto)

Em disco (local-first, inspecionável — nada de banco opaco):

    <data>/projetos/<slug>/
    ├── projeto.json            metadados do node
    ├── conversas/sessions/     ConversationStore escopado ao node
    ├── contexto/
    │   ├── contexto.md         contexto vivo do projeto
    │   └── anotacoes.jsonl     anotações datadas (append)
    └── artefatos/              recursos gerados

Interfaces: tool `projeto` (37ª — o cérebro opera os nodes) · CLI
`pluto projeto …` (o operador) · /api/chat aceita "projeto" (a conversa
nasce DENTRO do node). D2: tudo fica na máquina.
"""
from __future__ import annotations

import json
import os
import re
import time
import unicodedata
from pathlib import Path


def _agora() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def slugificar(nome: str) -> str:
    """Nome → slug seguro (a-z0-9-): determinístico, sem acento, SEM
    travessia de diretório ("../etc/passwd" vira "etc-passwd")."""
    txt = unicodedata.normalize("NFD", str(nome or "").strip().lower())
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    txt = re.sub(r"[^a-z0-9]+", "-", txt).strip("-")
    return txt[:40].strip("-")


def raiz(cfg) -> Path:
    return Path(cfg.data_dir) / "projetos"


def _dir(cfg, slug: str) -> Path:
    return raiz(cfg) / slugificar(slug)


def _meta_path(cfg, slug: str) -> Path:
    return _dir(cfg, slug) / "projeto.json"


def _atomic_write(path: Path, texto: str) -> None:
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(texto, encoding="utf-8")
    os.replace(tmp, path)              # crash no meio não corrompe


def _limpo(node: dict) -> dict:
    """Sem as contagens (elas são calculadas, não persistidas)."""
    return {k: v for k, v in node.items() if not k.startswith("n_")}


def _exigir(cfg, slug: str) -> dict:
    node = obter(cfg, slug)
    if node is None:
        raise ValueError(
            f"projeto '{slugificar(slug) or '(vazio)'}' não existe")
    return node


def _touch(cfg, slug: str) -> None:
    p = _meta_path(cfg, slug)
    if p.exists():
        try:
            node = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        node["atualizado_em"] = _agora()
        _atomic_write(p, json.dumps(node, ensure_ascii=False, indent=1))


# ------------------------------------------------------------- CRUD do node
def criar(cfg, nome: str, descricao: str = "") -> dict:
    slug = slugificar(nome)
    if not slug:
        raise ValueError("nome de projeto inválido (sem letras/números)")
    if _meta_path(cfg, slug).exists():
        raise ValueError(f"projeto '{slug}' já existe")
    for sub in ("conversas/sessions", "contexto", "artefatos"):
        (_dir(cfg, slug) / sub).mkdir(parents=True, exist_ok=True)
    node = {
        "slug": slug,
        "nome": str(nome).strip() or slug,
        "descricao": str(descricao or "").strip(),
        "status": "ativo",
        "criado_em": _agora(),
        "atualizado_em": _agora(),
    }
    _atomic_write(_meta_path(cfg, slug),
                  json.dumps(node, ensure_ascii=False, indent=1))
    return node


def obter(cfg, slug: str) -> dict | None:
    s = slugificar(slug)
    if not s:
        return None
    p = _meta_path(cfg, s)
    if not p.exists():
        return None
    try:
        node = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(node, dict) or not node.get("slug"):
        return None
    # contagens vivem na hora (node honesto: o que há DENTRO dele)
    node["n_conversas"] = len(conversas_do(cfg, s))
    node["n_anotacoes"] = _anotacoes(cfg, s)[0]
    node["n_artefatos"] = len(artefatos_do(cfg, s))
    return node


def listar(cfg) -> list[dict]:
    out: list[dict] = []
    if not raiz(cfg).exists():
        return out
    for p in sorted(raiz(cfg).glob("*/projeto.json")):
        try:
            node = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(node, dict) and node.get("slug"):
            got = obter(cfg, node["slug"])
            if got:
                out.append(got)
    out.sort(key=lambda n: str(n.get("atualizado_em", "")), reverse=True)
    return out


# ---------------------------------------------------------------- conversas
def store_do(cfg, slug: str):
    """ConversationStore escopado ao node (mesma convenção de path,
    uma fonte só — ver conversations.ConversationStore)."""
    from .conversations import ConversationStore
    return ConversationStore(cfg, projeto=slugificar(slug))


def conversas_do(cfg, slug: str) -> list[dict]:
    return store_do(cfg, slug).list()


# ----------------------------------------------------------------- contexto
def _anotar_path(cfg, slug: str) -> Path:
    return _dir(cfg, slug) / "contexto" / "anotacoes.jsonl"


def _anotacoes(cfg, slug: str) -> tuple[int, list[dict]]:
    p = _anotar_path(cfg, slug)
    if not p.exists():
        return 0, []
    linhas: list[dict] = []
    for ln in p.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            obj = json.loads(ln)
        except json.JSONDecodeError:
            continue          # linha parcial (crash antigo) é pulada
        if isinstance(obj, dict) and obj.get("texto"):
            linhas.append(obj)
    return len(linhas), linhas


def anotar(cfg, slug: str, texto: str) -> dict:
    _exigir(cfg, slug)
    t = str(texto or "").strip()
    if not t:
        raise ValueError("anotação vazia")
    linha = {"ts": _agora(), "texto": t}
    _anotar_path(cfg, slug).parent.mkdir(parents=True, exist_ok=True)
    with _anotar_path(cfg, slug).open("a", encoding="utf-8") as f:
        f.write(json.dumps(linha, ensure_ascii=False) + "\n")
    _touch(cfg, slug)
    return linha


def ler_contexto(cfg, slug: str) -> str:
    _exigir(cfg, slug)
    partes: list[str] = []
    md = _dir(cfg, slug) / "contexto" / "contexto.md"
    if md.exists():
        txt = md.read_text(encoding="utf-8").strip()
        if txt:
            partes.append(txt)
    _, notas = _anotacoes(cfg, slug)
    if notas:
        partes.append("Anotações:\n" + "\n".join(
            f"- [{n.get('ts', '')}] {n['texto']}" for n in notas[-10:]))
    return "\n\n".join(partes)


# ----------------------------------------------------------------- artefatos
def artefatos_do(cfg, slug: str) -> list[str]:
    d = _dir(cfg, slug) / "artefatos"
    if not d.exists():
        return []
    return sorted(p.name for p in d.iterdir() if p.is_file())


def salvar_artefato(cfg, slug: str, nome: str, conteudo: str) -> dict:
    _exigir(cfg, slug)
    n = str(nome or "").strip()
    if (not n or "/" in n or "\\" in n or n in (".", "..")
            or n.startswith(".")):
        raise ValueError("nome de artefato inválido")
    path = _dir(cfg, slug) / "artefatos" / n
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(conteudo or ""), encoding="utf-8")
    _touch(cfg, slug)
    return {"projeto": slugificar(slug), "artefato": n,
            "caminho": str(path), "bytes": path.stat().st_size}


# ------------------------------------------------------------------- status
def _mudar_status(cfg, slug: str, status: str) -> dict:
    node = _exigir(cfg, slug)
    node["status"] = status
    node["atualizado_em"] = _agora()
    _atomic_write(_meta_path(cfg, slug),
                  json.dumps(_limpo(node), ensure_ascii=False, indent=1))
    return node


def arquivar(cfg, slug: str) -> dict:
    return _mudar_status(cfg, slug, "arquivado")


def reativar(cfg, slug: str) -> dict:
    return _mudar_status(cfg, slug, "ativo")


# ------------------------------------------------------------------- árvore
def arvore(cfg, slug: str | None = None) -> str:
    """O node em texto — a árvore que o operador desenhou:
    projeto → conversas · contexto · artefatos."""
    if not (slug or "").strip():
        nodes = listar(cfg)
        if not nodes:
            return ("nenhum projeto ainda — crie com a tool projeto "
                    "(acao criar) ou: pluto projeto criar <nome>")
        linhas = ["📁 projetos (nodes):"]
        for n in nodes:
            estado = "" if n.get("status") == "ativo" else " [arquivado]"
            linhas.append(
                f"- {n['slug']}{estado} — {n.get('nome', '')} "
                f"({n['n_conversas']} conversa(s) · "
                f"{n['n_anotacoes']} anotação(ões) · "
                f"{n['n_artefatos']} artefato(s))")
        return "\n".join(linhas)
    node = _exigir(cfg, slug)
    s = node["slug"]
    arts = artefatos_do(cfg, s)
    arts_txt = (": " + " · ".join(arts[:8]) + (" …" if len(arts) > 8 else "")
                if arts else "")
    estado = "" if node.get("status") == "ativo" else " [arquivado]"
    desc = f" — {node['descricao']}" if node.get("descricao") else ""
    tem_md = (_dir(cfg, s) / "contexto" / "contexto.md").exists()
    return "\n".join([
        f"📁 projeto: {s}{estado} ({node.get('nome', s)}{desc})",
        f"├── conversas: {node['n_conversas']}",
        f"├── contexto: {node['n_anotacoes']} anotação(ões)"
        + (" + contexto.md" if tem_md else ""),
        f"└── artefatos: {node['n_artefatos']}{arts_txt}",
        f"caminho: {_dir(cfg, s)}",
    ])


# ---------------------------------------------------------------------- CLI
def cmd(args, cfg) -> None:
    """`pluto projeto <acao> [nome] [texto…]` — acoes: arvore (default),
    criar, anotar, contexto, arquivar, reativar. (Salvar artefato é
    tarefa do AGENTE via tool — no CLI o operador edita o arquivo.)"""
    from .contratos import acao_de
    a = acao_de(args, "arvore")
    nome = str(getattr(args, "nome", None) or "").strip()
    texto = " ".join(getattr(args, "texto", None) or []).strip()
    try:
        if a == "arvore":
            print(arvore(cfg, nome or None))
        elif a == "criar":
            node = criar(cfg, nome, texto)
            print(f"✔ projeto '{node['slug']}' criado")
        elif a == "anotar":
            anotar(cfg, nome, texto)
            print(f"✔ anotação registrada em '{slugificar(nome)}'")
        elif a == "contexto":
            print(ler_contexto(cfg, nome) or "(contexto vazio)")
        elif a == "arquivar":
            arquivar(cfg, nome)
            print(f"✔ projeto '{slugificar(nome)}' arquivado")
        elif a == "reativar":
            reativar(cfg, nome)
            print(f"✔ projeto '{slugificar(nome)}' reativado")
        else:
            print(f"✖ ação desconhecida: {a} "
                  "(arvore|criar|anotar|contexto|arquivar|reativar)")
    except ValueError as e:
        print(f"✖ {e}")
