"""V9.0.0 (P4 · T247–T248): O SECRETÁRIO PROATIVO — "me dando tempo
para estudos e outras atividades".

O agente deixa de ser reativo: ele TOMA A INICIATIVA de avisar.

- **Briefing diário** (``briefing_on``, ``briefing_hora``): 1 mensagem
  no Telegram pela manhã com agenda do dia, e-mails não lidos
  (triados), tarefas ativas (checkpoints da P1) e o que ficou no
  diário de ontem. Falha de envio RETENTA com backoff de 1 h e nunca
  é silenciosa (notify + log).
- **Lembretes** (``lembrete_min``, default 30): evento da agenda
  começando dentro da janela → aviso no Telegram; cada evento é
  lembrado 1× por dia (registry), sem spam.
- **Triagem de e-mail** (``email_triagem_on``): não lidos do IMAP
  (Gmail/Microsoft vinculados na página Contas) classificados em
  "precisa de você" (fatura/prazo/pergunta) × informativo — o resumo
  entra no briefing.

Tudo injetável (``_canal``/``_agenda``/``_emails``…) — testes sem
rede. ``tick()`` é chamado pelo Scheduler a cada ciclo (15 s), com
rate-limit próprio (lembretes checam a cada 5 min). Local-first:
registries em data_dir; nada sai da máquina exceto o envio explícito
ao canal do operador.
"""
from __future__ import annotations

import json
import re as _re
import time
from datetime import datetime, timedelta
from pathlib import Path

# janela de checagem dos lembretes no tick (não martela a API a cada 15s)
_INTERVALO_LEMBRETE_S = 300
# após uma falha de envio, retenta no máximo 1× por hora
_BACKOFF_FALHA_S = 3600

# assuntos que pedem ação do operador (triagem heurística PT-BR)
_PRECISA_DE_VOCE = (
    "vence", "venciment", "fatura", "boleto", "pagament", "pagar",
    "prazo", "responda", "responder", "urgente", "pendente",
    "ação necessária", "acao necessaria", "confirme", "confirmaç",
    "sua senha", "verificaç", "atualize seus dados", "multa", "cobran",
)


# ─────────────────────────────────────────────────── registro interno
def _registro(cfg) -> dict:
    p = Path(cfg.data_dir) / "secretario.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _salvar_registro(cfg, reg: dict) -> None:
    try:
        p = Path(cfg.data_dir) / "secretario.json"
        p.write_text(json.dumps(reg, ensure_ascii=False, indent=1),
                     encoding="utf-8")
    except OSError:
        pass


def _lembretes_dados(cfg) -> set[str]:
    try:
        return set(json.loads(
            (Path(cfg.data_dir) / "lembretes.json").read_text(
                encoding="utf-8")))
    except Exception:  # noqa: BLE001
        return set()


def _marcar_lembrete(cfg, chaves: set[str]) -> None:
    try:
        p = Path(cfg.data_dir) / "lembretes.json"
        p.write_text(json.dumps(sorted(chaves), ensure_ascii=False),
                     encoding="utf-8")
    except OSError:
        pass


# ─────────────────────────────────────────────────── canal do operador
def _canal_default(cfg):
    """CanalTelegram quando configurado; None caso contrário."""
    try:
        from .telegram_gw import CanalTelegram
        c = CanalTelegram(cfg)
        return c if c.disponivel() else None
    except Exception:  # noqa: BLE001
        return None


def _avisar(cfg, canal, texto: str) -> None:
    """Entrega no melhor canal disponível — nunca silencioso."""
    if canal is not None:
        canal.enviar(texto)
        return
    try:
        from .notify import push
        push(cfg, "secretario", "Pluto — aviso", texto)
    except Exception:  # noqa: BLE001
        pass


# ─────────────────────────────────────────────────── triagem de e-mail
def _dec_cab(valor: str) -> str:
    try:
        from email.header import decode_header, make_header
        return str(make_header(decode_header(valor)))
    except Exception:  # noqa: BLE001
        return valor


def _cab(bruto: str, campo: str, padrao: str) -> str:
    """Valor decodificado de um cabeçalho do bloco bruto IMAP."""
    m = _re.search(rf"^{campo}:\s*(.+)$", bruto, _re.M | _re.I)
    return _dec_cab(m.group(1).strip()) if m else padrao


def _ler_nao_lidos(cfg, limite: int = 10) -> list[dict]:
    """Não lidos via IMAP das contas vinculadas (página Contas).
    best-effort: conta fora do ar não derruba as demais."""
    import imaplib

    from . import emailcfg

    accs = (emailcfg.load(cfg).get("accounts") or [])[:3]
    out: list[dict] = []
    for acc in accs:
        M = None
        try:
            tls = acc.get("imap_tls", "ssl")
            if tls == "none":
                M = imaplib.IMAP4(acc["imap_host"],
                                  int(acc.get("imap_port", 143)), timeout=20)
            else:
                M = imaplib.IMAP4_SSL(acc["imap_host"],
                                      int(acc.get("imap_port", 993)),
                                      timeout=20)
            if acc.get("auth") == "oauth":
                tok = emailcfg.refresh_access_token(acc)
                M.authenticate("XOAUTH2", _xoauth_factory(acc, tok))
            else:
                M.login(acc["user"], acc["password"])
            M.select("INBOX", readonly=True)
            _typ, ids = M.search(None, "UNSEEN")
            for num in (ids[0].split() or [])[-limite:]:
                _t, d = M.fetch(
                    num, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT)])")
                bruto = b"".join(p[1] for p in d
                                 if isinstance(p, tuple)).decode(
                                     "utf-8", "replace")
                out.append({"de": _cab(bruto, "From", "(remetente ?)")[:80],
                            "assunto": _cab(bruto, "Subject",
                                            "(sem assunto)")[:120],
                            "conta": str(acc.get("user") or "")})
                if len(out) >= limite:
                    break
        except Exception:  # noqa: BLE001
            continue
        finally:
            if M is not None:
                try:
                    M.logout()
                except Exception:  # noqa: BLE001
                    pass
    return out[:limite]


def _xoauth_factory(acc: dict, tok: str):
    from .emailcfg import xoauth2_string

    def _cb(_challenge):
        return xoauth2_string(acc["user"], tok)
    return _cb


def triar_emails(cfg, limite: int = 10, _ler=None) -> dict:
    """Não lidos classificados: 'precisa de você' × informativo."""
    emails = (_ler(cfg, limite) if _ler is not None
              else _ler_nao_lidos(cfg, limite))
    precisa, info = [], []
    for e in emails:
        alvo = (str(e.get("assunto", "")) + " " + str(e.get("de", ""))).lower()
        if any(k in alvo for k in _PRECISA_DE_VOCE) or \
                str(e.get("assunto", "")).strip().endswith("?"):
            precisa.append(e)
        else:
            info.append(e)
    if not emails:
        resumo = "nenhum e-mail não lido"
    else:
        resumo = (f"{len(emails)} não lido(s) · {len(precisa)} precisa(m) "
                  f"de você · {len(info)} informativo(s)")
        if precisa:
            resumo += (" — ex.: " + precisa[0]["assunto"][:60])
    return {"total": len(emails), "precisa": precisa, "info": info,
            "resumo": resumo}


# ─────────────────────────────────────────────────────── briefing
def _agenda_texto(cfg) -> str:
    try:
        from . import agendacfg
        return agendacfg.list_events(cfg, dias=1) or "nenhum evento hoje"
    except Exception as exc:  # noqa: BLE001  (sem conta = degradação honesta)
        return f"— agenda não conectada ({str(exc)[:60]}… página Contas)"


def montar_briefing(cfg, _agenda=None, _tarefas=None, _emails=None,
                    _diario=None) -> dict:
    """O conteúdo do briefing (estruturado + texto pronto p/ enviar)."""
    agenda = (_agenda(cfg) if _agenda is not None else _agenda_texto(cfg))
    if _tarefas is not None:
        tarefas = _tarefas(cfg)
    else:
        try:
            from . import contexto
            tarefas = contexto.listar(cfg)
        except Exception:  # noqa: BLE001
            tarefas = []
    if _emails is not None:
        emails = _emails(cfg)
    elif bool(getattr(cfg, "email_triagem_on", False)):
        emails = triar_emails(cfg)
    else:
        emails = None
    if _diario is not None:
        ontem = _diario(cfg)
    else:
        try:
            from . import contexto
            ontem = contexto.diario_ler(
                cfg, dia=(datetime.now() - timedelta(days=1)).strftime(
                    "%Y-%m-%d"))
        except Exception:  # noqa: BLE001
            ontem = []

    linhas = [f"☀️ BOM DIA — briefing do Pluto "
              f"({datetime.now().strftime('%d/%m %H:%M')})", ""]
    linhas.append(f"🗓 Agenda de hoje:\n{agenda}")
    if tarefas:
        linhas.append("📋 Tarefas ativas:")
        linhas += [f"  • {t.get('id')} — "
                   f"{str(t.get('objetivo', ''))[:80]}" for t in tarefas[:5]]
    else:
        linhas.append("📋 Tarefas ativas: nenhuma em andamento")
    if emails is not None:
        linhas.append(f"📧 E-mails: {emails['resumo']}")
        for e in emails["precisa"][:3]:
            linhas.append(f"    ⚠ {e['assunto'][:70]} ({e['de'][:30]})")
    if ontem:
        linhas.append("📓 Ontem no diário:")
        linhas += [f"  • {e.get('o_que', '')[:80]}" for e in ontem[-4:]]
    return {"ok": True, "texto": "\n".join(linhas), "agenda": agenda,
            "tarefas": tarefas, "emails": emails, "diario": ontem}


def enviar_briefing(cfg, _canal=None) -> dict:
    """Monta e entrega o briefing no canal do operador."""
    br = montar_briefing(cfg)
    canal = _canal if _canal is not None else _canal_default(cfg)
    if canal is None:
        _avisar(cfg, None, "briefing pronto mas Telegram não configurado "
                           "— pluto telegram start")
        return {"ok": False,
                "msg": "Telegram não configurado — pluto telegram start "
                       "(briefing impresso no notify)", "texto": br["texto"]}
    canal.enviar(br["texto"])
    return {"ok": True, "msg": "briefing enviado", "texto": br["texto"]}


# ─────────────────────────────────────────────────────── lembretes
def checar_lembretes(cfg, agora: datetime | None = None,
                     _eventos=None, _canal=None) -> list[dict]:
    """Eventos começando dentro da janela lembrete_min → 1 aviso cada."""
    agora = agora or datetime.now().astimezone()
    if _eventos is not None:
        eventos = _eventos(cfg)
    else:
        try:
            from . import agendacfg
            eventos = agendacfg.eventos_estruturados(cfg, dias=1)
        except Exception:  # noqa: BLE001
            eventos = []
    janela_min = int(getattr(cfg, "lembrete_min", 30) or 0)
    if janela_min <= 0 or not eventos:
        return []
    canal = _canal if _canal is not None else _canal_default(cfg)
    ja = _lembretes_dados(cfg)
    hoje = agora.strftime("%Y-%m-%d")
    enviados = []
    for ev in eventos:
        ini = ev.get("inicio")
        if not isinstance(ini, datetime):
            continue
        faltam = (ini - agora).total_seconds() / 60.0
        if not (0 <= faltam <= janela_min):
            continue
        chave = f"{hoje}:{ev['titulo'][:60]}:{ini.strftime('%H:%M')}"
        if chave in ja:
            continue
        _avisar(cfg, canal,
                f"⏰ em {int(faltam)} min: {ev['titulo'][:80]}"
                + (f" · 📍 {ev['local'][:40]}" if ev.get("local") else ""))
        ja.add(chave)
        enviados.append(ev)
    if enviados:
        _marcar_lembrete(cfg, ja)
    return enviados


# ─────────────────────────────────────────────────────────── tick
def tick(cfg, _agora=None, _canal=None, _agenda=None, _emails=None) -> None:
    """Chamado pelo Scheduler a cada ciclo (15 s) — best-effort, nunca
    levanta. Briefing 1×/dia no horário configurado (falha retenta 1×/h);
    lembretes checados a cada 5 min."""
    agora = _agora or datetime.now()
    try:
        reg = _registro(cfg)
        # ── briefing diário
        if bool(getattr(cfg, "briefing_on", False)):
            hoje = agora.strftime("%Y-%m-%d")
            hora_cfg = str(getattr(cfg, "briefing_hora", "07:00") or "07:00")
            try:
                hh, mm = (int(x) for x in hora_cfg.split(":")[:2])
            except ValueError:
                hh, mm = 7, 0
            devido = (agora.hour, agora.minute) >= (hh, mm)
            enviado_hoje = reg.get("briefing_data") == hoje
            ultima_tent = float(reg.get("briefing_tentativa", 0) or 0)
            em_backoff = (time.time() - ultima_tent) < _BACKOFF_FALHA_S
            if devido and not enviado_hoje and not em_backoff:
                reg["briefing_tentativa"] = time.time()
                _salvar_registro(cfg, reg)      # marca ANTES (não spam)
                r = enviar_briefing(cfg, _canal=_canal)
                if r.get("ok"):
                    reg["briefing_data"] = hoje
                    reg["briefing_tentativa"] = 0   # sucesso zera o backoff
                _salvar_registro(cfg, reg)
        # ── lembretes (a cada 5 min)
        if int(getattr(cfg, "lembrete_min", 30) or 0) > 0:
            if time.time() - float(reg.get("lembrete_check", 0) or 0) \
                    >= _INTERVALO_LEMBRETE_S:
                reg["lembrete_check"] = time.time()
                _salvar_registro(cfg, reg)
                if _agenda is not None or _canal is not None:
                    checar_lembretes(cfg, agora=agora, _eventos=_agenda,
                                     _canal=_canal)
                else:
                    checar_lembretes(cfg, agora=agora)
    except Exception as exc:  # noqa: BLE001  (nunca derruba o scheduler)
        try:
            from . import activity
            activity.log(cfg, "secretario", f"⚠ tick: {exc}")
        except Exception:  # noqa: BLE001
            pass
