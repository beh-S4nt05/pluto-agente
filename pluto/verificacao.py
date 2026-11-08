"""V9.0.0 (P2 · T245): VERIFICAÇÃO DE 2ª PASSADA — anti-alucinação.

Depois de gerar uma resposta que usa ferramentas, uma passada BARATA
confere cada AFIRMAÇÃO Factual contra os DADOS que as ferramentas
retornaram (macro-fluxo, estágio [6]):

- ✓ lastreada — os dados das tools sustentam a afirmação (evidência);
- ✗ sem lastro / contradita — número que não está nos dados,
  generalização apresentada como fato → CORRIGIR;
- ~ incerta — sem dados que sustentem → DECLARAR a incerteza na
  resposta (nunca entregar como fato).

Saídas: **score de confiança** (rodapé da resposta) e a regra dura:
**confiança baixa (ou qualquer ✗) + ação destrutiva →
`perguntar_operador` obrigatório** (a tool já existe — nada de
executar rm/deploy/envio com afirmações não verificadas).

Piso vs. topo (Princípio 0): no perfil leve roda o checklist
heurístico (determinístico, tokens ~0); com o portão
``verificacao_completa`` aberto (P7) o CÉREBRO faz a passada —
mesmo contrato, profundidade maior, fallback honesto.

Distinção com a P3: a autoavaliação confere a entrega CONTRA O
PEDIDO; a verificação confere as afirmações CONTRA OS DADOS das
ferramentas. As duas juntas fecham o estágio [6]+[7] do macro-fluxo.
"""
from __future__ import annotations

import json
import re
import time

from .autoavaliacao import _keywords, _sem_acento

# ─────────────────────────────────────────────── extração de afirmações
# verbos que tornam a frase uma afirmação factual verificável
# (formas com e sem acento — o casamento testa as duas)
_VERBOS_FACTUAIS = (
    "é", "são", "sao", "foi", "foram", "está", "esta", "estão", "estao",
    "estava", "têm", "tem", "havia", "houve", "roda", "rodou", "rodam",
    "rodaram", "executa", "executou", "executam", "passou", "passa",
    "passam", "falhou", "funciona", "funcionou", "custa", "custou",
    "retorna", "retornou", "retornam", "criou", "cria", "salvou",
    "salva", "instalou", "instala", "existe", "existem", "ficou",
    "fica", "subiu", "caiu", "gerou",
)
_ABSOLUTOS = ("sempre", "nunca", "jamais", "todos os", "todas as",
              "todo o", "toda a", "nenhum", "nenhuma", "ninguem")
_MENOS_QUE_FATO = ("acho", "talvez", "possivelmente", "imagino", "parece",
                   "provavelmente", "creio", "suspeito")

_RE_SENTENCA = re.compile(r"[.!?;\n]+")
_RE_NUMEROS = re.compile(r"\d+(?:[.,]\d+)?")
_MAX_AFF = 8


def extrair_afirmacoes(resposta: str) -> list[str]:
    """Afirmações factuais verificáveis — determinístico (auditável)."""
    texto = (resposta or "").strip()
    if not texto:
        return []
    saida: list[str] = []
    vistos: set[str] = set()
    for frase in _RE_SENTENCA.split(texto):
        seg = frase.strip(" ,;:-–—")
        if len(seg) < 6:
            continue
        orig = " " + seg.lower() + " "     # com acentos (verbos)
        baixo = " " + _sem_acento(seg) + " "   # sem acentos
        if any(m in baixo for m in _MENOS_QUE_FATO):
            continue                      # opinião declarada ≠ fato
        tem_num = bool(_RE_NUMEROS.search(seg))
        tem_verbo = any(f" {v} " in orig or f" {v} " in baixo
                        for v in _VERBOS_FACTUAIS)
        tem_abs = any(a in baixo for a in _ABSOLUTOS)
        if not (tem_num or tem_verbo or tem_abs):
            continue
        chave = _sem_acento(seg)[:80]
        if chave in vistos:
            continue
        vistos.add(chave)
        saida.append(seg)
    return saida[:_MAX_AFF]


# ─────────────────────────────────────────────── checagem heurística
def _checar(afirmacao: str, dados: str) -> tuple[str, str]:
    """(status, evidência) — ✓ lastreada · ✗ sem lastro · ~ incerta."""
    palha = _sem_acento(dados or "")
    nums = _RE_NUMEROS.findall(afirmacao or "")
    faltam = [n for n in nums
              if n not in palha and n.replace(".", ",") not in palha]
    if faltam:
        return ("✗", f"número sem lastro nos dados das ferramentas: "
                      f"{', '.join(faltam)}")
    if nums:
        return ("✓", f"número(s) conferido(s) nos dados: "
                      f"{', '.join(nums[:3])}")
    baixo = " " + _sem_acento(afirmacao) + " "
    if any(a in baixo for a in _ABSOLUTOS):
        return ("~", "generalização sem lastro nos dados — declare "
                     "incerteza ou remova o absoluto")
    kws = _keywords(afirmacao)
    if not kws:
        return ("~", "afirmação sem termos cruzáveis com os dados")
    achados = [k for k in kws if k in palha]
    if len(achados) * 2 >= len(kws):
        return ("✓", f"sustentada pelos dados (termos: "
                      f"{', '.join(achados[:3])})")
    return ("~", "sem dados que sustentem — declare incerteza na resposta")


# ─────────────────────────────────────────────── passada pelo cérebro
_PROMPT_VERIFICACAO = """\
Você é a 2ª PASSADA de verificação de um agente. Confira CADA afirmação
da RESPOSTA contra os DADOS reais das ferramentas — nada além disso é
evidência (não use conhecimento do mundo).

RESPOSTA PRODUZIDA:
{resposta}

DADOS DAS FERRAMENTAS (saídas reais):
{dados}

AFIRMAÇÕES:
{afirmacoes}

Responda APENAS com JSON:
{{"afirmacoes": [{{"status": "ok|incerto|violado",
 "evidencia": "<o que nos dados sustenta ou contradiz>"}}]}}
Regras: um veredito por afirmação, na MESMA ordem; "violado" só se o
dado contradiz ou o número não tem lastro; sem dados → "incerto"
(nunca invente evidência)."""


_STATUS_MAP = {"ok": "✓", "incerto": "~", "violado": "✗"}

# abaixo disto, ação destrutiva é PROIBIDA sem perguntar ao operador
CONF_MINIMA_DESTRUTIVA = 80


def _julgar_cerebro(cfg, prompt: str) -> str:
    """1 completion no modelo LOCAL (nada sai da máquina — D2).
    Indisponível → "" (fallback heurístico, honesto)."""
    try:
        from .ollama_client import OllamaClient, timeout_resposta
        cli = OllamaClient(cfg.ollama_url, timeout=timeout_resposta(cfg))
        partes = []
        for ch in cli.chat_stream("", [{"role": "user", "content": prompt}]):
            t = (ch.get("message") or {}).get("content") or ""
            if t:
                partes.append(t)
        return "".join(partes).strip()
    except Exception:  # noqa: BLE001
        return ""


def verificar(cfg, resposta: str, dados_tools: str = "",
              acao_destrutiva: bool = False, _julgar=None) -> dict:
    """2ª passada: afirmações da resposta vs. dados das ferramentas.

    {"ok": True, "afirmacoes": [{texto, status, evidencia}],
     "confianca": int|None, "veredicto": str, "metodo": str,
     "rodape": str, "motivo": str}
    """
    from .capacidades import capacidades
    cap = capacidades(cfg)
    afirmacoes = extrair_afirmacoes(resposta)
    if not afirmacoes:
        res = {"ok": True, "afirmacoes": [], "confianca": None,
               "veredicto": "entregar", "metodo": "heuristica",
               "perfil": cap.perfil,
               "motivo": "nenhuma afirmação factual verificável na "
                         "resposta"}
        res["rodape"] = rodape(res)
        _auditar(cfg, res)
        return res

    usar_cerebro = (_julgar is not None
                    or (not getattr(cfg, "mock", False)
                        and cap.aberto("verificacao_completa")))
    metodo = "heuristica"
    checagens: list[dict] = []
    if usar_cerebro:
        prompt = _PROMPT_VERIFICACAO.format(
            resposta=(resposta or "")[:1500],
            dados=(dados_tools or "")[:2500] or "(nenhum)",
            afirmacoes="\n".join(f"{i + 1}. {a}"
                                 for i, a in enumerate(afirmacoes)))
        raw = (_julgar(prompt) if _julgar is not None
               else _julgar_cerebro(cfg, prompt))
        if raw:
            try:
                from .extrair import json_de
                j = json_de(raw) or {}
                lista = j.get("afirmacoes") if isinstance(j, dict) else None
                if isinstance(lista, list) and len(lista) == len(afirmacoes):
                    for i, item in enumerate(lista):
                        st = _STATUS_MAP.get(str(item.get("status", ""))
                                             .strip().lower())
                        if st is None:
                            raise ValueError("status inválido")
                        checagens.append(
                            {"texto": afirmacoes[i], "status": st,
                             "evidencia": str(
                                 item.get("evidencia", ""))[:200]})
                    metodo = "cerebro"
            except Exception:  # noqa: BLE001
                checagens = []        # JSON torto → heurística (honesto)
    if not checagens:
        for a in afirmacoes:
            st, ev = _checar(a, dados_tools or "")
            checagens.append({"texto": a, "status": st, "evidencia": ev})

    n_ok = sum(1 for c in checagens if c["status"] == "✓")
    n_mal = sum(1 for c in checagens if c["status"] == "✗")
    confianca = round(100 * n_ok / len(checagens))
    destrutiva = bool(acao_destrutiva)
    if n_mal:
        veredicto, motivo = "corrigir", (f"{n_mal} afirmação(ões) SEM "
                                         "lastro nos dados — corrija ou "
                                         "declare incerteza")
    elif any(c["status"] == "~" for c in checagens):
        veredicto = "declarar-incertezas"
        motivo = "há afirmações sem dados que as sustentem — declare-as"
    else:
        veredicto, motivo = "entregar", "todas as afirmações lastreadas"
    # REGRA DURA (pedido do operador): incerto/erro + destrutivo →
    # PERGUNTAR, nunca executar às cegas
    if destrutiva and (n_mal or confianca < CONF_MINIMA_DESTRUTIVA):
        veredicto = "perguntar-operador"
        motivo = (f"ação DESTRUTIVA com confiança {confianca}% "
                  f"(mínimo {CONF_MINIMA_DESTRUTIVA}%)"
                  + (f" e {n_mal} ✗" if n_mal else "")
                  + " — chame perguntar_operador ANTES de executar")
    res = {"ok": True, "afirmacoes": checagens, "confianca": confianca,
           "veredicto": veredicto, "metodo": metodo, "perfil": cap.perfil,
           "motivo": motivo, "acao_destrutiva": destrutiva}
    res["rodape"] = rodape(res)
    _auditar(cfg, res)
    return res


def rodape(res: dict) -> str:
    """Score de confiança no rodapé da resposta (auditável)."""
    if not res.get("afirmacoes"):
        return "🔎 Verificação: sem afirmações factuais verificáveis"
    n_ok = sum(1 for c in res["afirmacoes"] if c["status"] == "✓")
    n_mal = sum(1 for c in res["afirmacoes"] if c["status"] == "✗")
    n_inc = len(res["afirmacoes"]) - n_ok - n_mal
    conf = res.get("confianca")
    base = (f"🔎 Verificação: {n_ok}✓ · {n_mal}✗ · {n_inc}~ · "
            f"confiança {conf}%")
    if res.get("veredicto") == "perguntar-operador":
        return base + " — AÇÃO DESTRUTIVA: pergunte ao operador antes"
    if n_mal:
        return base + " — corrija os ✗ antes de entregar"
    if n_inc:
        return base + " — declare as incertezas (~) na resposta"
    return base


def _auditar(cfg, res: dict) -> None:
    """Quadro em verificacoes.jsonl (privado) + resumo no agent.log —
    o CONTEÚDO da resposta não vaza no log (padrão D2)."""
    try:
        path = cfg.data_dir / "verificacoes.jsonl"
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(
                {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                 "afirmacoes": len(res.get("afirmacoes") or []),
                 "confianca": res.get("confianca"),
                 "veredicto": res.get("veredicto"),
                 "metodo": res.get("metodo"),
                 "destrutiva": res.get("acao_destrutiva", False)},
                ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass
    try:
        from . import activity
        activity.log(cfg, "verificacao",
                     f"🔎 {len(res.get('afirmacoes') or [])} afirmação(ões) "
                     f"· confiança {res.get('confianca')}% · "
                     f"{res.get('veredicto')} · {res.get('metodo')}")
    except Exception:  # noqa: BLE001
        pass
