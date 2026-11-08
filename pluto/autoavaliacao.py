"""V9.0.0 (P3 · T246): AUTOAVALIAÇÃO — o agente confere a entrega
contra o PEDIDO antes de entregar.

Pedido do operador: "Deve se auto avaliar e verificar se está dentro
do que foi pedido e se o que está entregando e fazendo está dentro do
esperado corretamente."

Como funciona (macro-fluxo, estágio [7]):

1. ``extrair_criterios(pedido)`` — heurística determinística PT-BR:
   o pedido é partido em segmentos e cada segmento com MARCADOR de
   exigência (crie/deve/tem que/nunca…) ou QUANTIFICADOR (números)
   vira um critério verificável. Determinístico de propósito: os
   critérios são auditáveis — mesma entrada, mesma lista.
2. ``avaliar(cfg, pedido, entrega, dados_tools)`` — cada critério é
   julgado contra a entrega (e as SAÍDAS REAIS das ferramentas):
   ✅ cumprido (com evidência) · ✖ violado (número do pedido ausente,
   proibição presente) · ⚠️ não verificável (DIZ que não conseguiu).
   Julgamento por CÉREBRO quando o portão ``verificacao_completa``
   está aberto (P7) e o modelo está de pé — com fallback honesto para
   a heurística. Em mock: sempre heurística (determinístico).
3. Veredicto: algum ✖ → ``corrigir`` (não entregar) · só ⚠️ →
   ``revisar`` (entrega com ressalvas declaradas) · tudo ✅ →
   ``entregar``.
4. Auditoria: quadro completo em ``<data>/autoavaliacoes.jsonl`` +
   1 linha resumida no agent.log (o PEDIDO não vaza no log — padrão D2).

O perfil do cérebro calibra a PROFUNDIDADE (Princípio 0), nunca a
existência do estágio: leve = checklist heurístico; rapido/forte =
passada completa pelo cérebro.
"""
from __future__ import annotations

import json
import re
import time
import unicodedata

# ─────────────────────────────────────────────── extração de critérios
# marcadores de exigência (PT-BR, formulados ou coloquiais)
_MARCADORES = (
    "quero", "preciso", "precisa", "deve", "devem", "tem que", "tem de",
    "crie", "cria", "criar", "faca", "faz", "faça", "configure",
    "configura", "use", "usa", "usar", "instale", "instala", "adicione",
    "adiciona", "remova", "remove", "garanta", "garante", "garantir",
    "assegure", "certifique", "nao esqueca", "nunca", "sempre",
    "rode", "executa", "execute", "publique", "entregue", "mostre",
    "liste", "salve", "grave", "avise", "lembre", "agende", "escreva",
    "leia", "envie", "mantenha", "respeite", "sigam", "siga", "limite",
    "maximo", "máximo", "minimo", "mínimo", "proiba", "evite",
)

_STOPWORDS = set("""
que para com uma uns umas dos das pela pelas como quando onde qual
quais muito mais menos tambem tambem porque pois entao então assim
dele dela disso aqui estar ser ter sido feito fazer isso aquilo
minha meu meus minhas nosso nossa serao serão deve devem podem pode
quero precisa precisamos antes depois sobre entre ate até desde pelo
somente apenas todo toda todos todas outro outra outros outras
""".split())

_MAX_CRITERIOS = 8          # quadro legível no ctx 8k
_MAX_KEYWORDS = 6

_RE_SENTENCA = re.compile(r"[.!?;\n]+")
_RE_E_SEGUNDO = re.compile(
    r"\s+e\s+(?=(?:tambem|também|além|alem|por fim|depois)\b|"
    + "|".join(re.escape(m) for m in _MARCADORES) + r"\b)", re.I)
_RE_LIMPA = re.compile(
    r"^(?:e|além disso|alem disso|também|tambem|por fim|depois|que|"
    r"então|entao|por favor|pf)\s+", re.I)
_RE_NUMEROS = re.compile(r"\d+(?:[.,]\d+)?")
# proibição: pula o verbo comum e captura o OBJETO proibido
# ("nunca publique segredos" → proibido = "segredos")
_RE_PROIBICAO = re.compile(
    r"\b(?:n[aã]o\s+(?:deve|pode|quero)|nunca|jamais|proibido|sem)"
    r"(?:\s+(?:publique|publicar|publica|use|usar|usa|crie|criar|cria|"
    r"fa[cç]a|fazer|rode|rodar|roda|coloque|colocar|envie|enviar|"
    r"escreva|escrever|adicione|adicionar|mostre|mostrar|inclua|incluir|"
    r"deixe|deixar|salve|salvar|guarde|guardar|compartilhe|"
    r"compartilhar|exponha|expoe|expor))*\s+([\wà-ú-]+)", re.I)


def _sem_acento(txt: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", txt)
                   if unicodedata.category(c) != "Mn").lower()


def _keywords(texto: str) -> list[str]:
    """Palavras de conteúdo (sem acento, ≥4 chars, sem stopwords)."""
    palavras = [p for p in re.findall(r"[a-zà-ú0-9-]{4,}",
                                      _sem_acento(texto))]
    return [p for p in palavras
            if p not in _STOPWORDS and p not in _MARCADORES][:_MAX_KEYWORDS]


def extrair_criterios(pedido: str) -> list[str]:
    """Critérios verificáveis do pedido — determinístico e auditável."""
    texto = (pedido or "").strip()
    if not texto:
        return []
    segmentos: list[str] = []
    for frase in _RE_SENTENCA.split(texto):
        for parte in _RE_E_SEGUNDO.split(frase):
            seg = _RE_LIMPA.sub("", parte.strip(), count=1).strip(" ,;:-")
            if not seg or len(seg) < 6:
                continue
            baixo = _sem_acento(seg)
            tem_marca = any(m in baixo for m in _MARCADORES)
            tem_num = bool(_RE_NUMEROS.search(seg))
            if tem_marca or tem_num:
                segmentos.append(seg)
    # dedup (sem acento) preservando a ordem
    vistos, unicos = set(), []
    for seg in segmentos:
        chave = _sem_acento(seg)[:80]
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(seg)
    return unicos[:_MAX_CRITERIOS]


# ─────────────────────────────────────────────── avaliação heurística
def _avaliar_criterio(criterio: str, haystack: str) -> tuple[str, str]:
    """(status, evidência) — ✅ cumprido · ✖ violado · ⚠️ não verificável.

    Contratos objetivos (sem achismo):
    - número presente no critério e ausente na entrega → ✖;
    - proibição ("não deve X"/"nunca X"/"sem X") presente na entrega → ✖
      (e respeitada → ✅);
    - ≥ metade das keywords do critério na entrega → ✅; critério
      QUANTIFICADO com números conferidos + ao menos 1 termo → ✅
      (número verificado é evidência objetiva);
    - caso contrário → ⚠️ (declarado, nunca silencioso).
    """
    palha = _sem_acento(haystack or "")
    nums = _RE_NUMEROS.findall(criterio or "")
    faltam = [n for n in nums if n not in palha]
    if faltam:
        return ("✖", f"número(s) do pedido ausente(s) na entrega: "
                      f"{', '.join(faltam)}")
    m = _RE_PROIBICAO.search(criterio or "")
    if m:
        proibido = _sem_acento(m.group(1))
        if len(proibido) >= 4 and proibido in palha:
            return ("✖", f"proibição do pedido violada: "
                          f"'{m.group(1)}' aparece na entrega")
        return ("✅", f"proibição respeitada ('{m.group(1)}' não aparece)")
    kws = _keywords(criterio)
    if not kws:
        return ("⚠️", "critério sem termos verificáveis")
    achados = [k for k in kws if k in palha]
    if len(achados) * 2 >= len(kws):
        return ("✅", f"termos na entrega: {', '.join(achados[:3])}")
    if nums and achados:
        return ("✅", f"números conferidos ({', '.join(nums[:3])}); "
                      f"termo: {achados[0]}")
    return ("⚠️", f"não consegui verificar (termos ausentes: "
                  f"{', '.join([k for k in kws if k not in achados][:3])})")


# ─────────────────────────────────────────────── passada pelo cérebro
_PROMPT_JULGAMENTO = """\
Você é o VERIFICADOR de um agente. Julgue se a ENTREGA cumpre CADA
critério do PEDIDO — usando SOMENTE o que está na entrega e nos dados
das ferramentas (nada além disso é evidência).

PEDIDO:
{pedido}

ENTREGA (resposta produzida):
{entrega}

DADOS DAS FERRAMENTAS (saídas reais):
{dados}

CRITÉRIOS:
{criterios}

Responda APENAS com JSON:
{{"criterios": [{{"texto": "<critério>", "status": "ok|incerto|violado",
 "evidencia": "<o que sustenta o julgamento>"}}],
 "observacao": "<uma linha, opcional>"}}
Regras: um julgamento por critério, na MESMA ordem; "violado" só com
contradição concreta; sem evidência → "incerto" (nunca invente)."""


def _julgar_cerebro(cfg, prompt: str) -> str:
    """1 completion no modelo LOCAL (nada sai da máquina — padrão D2).
    Indisponível → "" (o chamador cai na heurística, honesto)."""
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


_STATUS_MAP = {"ok": "✅", "incerto": "⚠️", "violado": "✖"}


def avaliar(cfg, pedido: str, entrega: str, dados_tools: str = "",
            _julgar=None) -> dict:
    """Autoavalia a entrega contra o pedido — devolve o quadro auditável.

    {"ok": True, "criterios": [{texto, status, evidencia}], "score": int,
     "veredicto": "entregar|corrigir|revisar", "metodo": str,
     "perfil": str, "motivo": str}
    """
    from .capacidades import capacidades
    cap = capacidades(cfg)
    criterios = extrair_criterios(pedido or "")
    if not criterios:
        res = {"ok": True, "criterios": [], "score": 0, "veredicto": "revisar",
               "metodo": "heuristica", "perfil": cap.perfil,
               "motivo": "não extraí critérios verificáveis do pedido "
                         "(reformule ou confira manualmente)"}
        _auditar(cfg, res, pedido)
        return res

    # P7 (Princípio 0): o portão calibra a PROFUNDIDADE — o estágio
    # sempre existe; cérebro só julga com verificacao_completa aberto.
    usar_cerebro = (_julgar is not None
                    or (not getattr(cfg, "mock", False)
                        and cap.aberto("verificacao_completa")))
    metodo = "heuristica"
    julgados: list[dict] = []
    if usar_cerebro:
        prompt = _PROMPT_JULGAMENTO.format(
            pedido=(pedido or "")[:800], entrega=(entrega or "")[:2000],
            dados=(dados_tools or "")[:2000] or "(nenhum)",
            criterios="\n".join(f"{i + 1}. {c}"
                                for i, c in enumerate(criterios)))
        raw = (_julgar(prompt) if _julgar is not None
               else _julgar_cerebro(cfg, prompt))
        if raw:
            try:
                from .extrair import json_de
                j = json_de(raw) or {}
                lista = j.get("criterios") if isinstance(j, dict) else None
                if isinstance(lista, list) and len(lista) == len(criterios):
                    for i, item in enumerate(lista):
                        st = _STATUS_MAP.get(str(item.get("status", ""))
                                             .strip().lower())
                        if st is None:
                            raise ValueError("status inválido")
                        julgados.append({"texto": criterios[i], "status": st,
                                         "evidencia": str(
                                             item.get("evidencia", ""))[:200]})
                    metodo = "cerebro"
            except Exception:  # noqa: BLE001
                julgados = []        # JSON torto → heurística (honesto)
    if not julgados:
        for c in criterios:
            st, ev = _avaliar_criterio(c, (entrega or "") + "\n"
                                       + (dados_tools or ""))
            julgados.append({"texto": c, "status": st, "evidencia": ev})

    n_ok = sum(1 for j in julgados if j["status"] == "✅")
    n_mal = sum(1 for j in julgados if j["status"] == "✖")
    score = round(100 * n_ok / len(julgados))
    if n_mal:
        veredicto, motivo = "corrigir", (f"{n_mal} critério(s) VIOLADO(s) — "
                                         "corrija antes de entregar")
    elif any(j["status"] == "⚠️" for j in julgados):
        veredicto = "revisar"
        motivo = "há pontos que não consegui verificar — declare-os"
    else:
        veredicto, motivo = "entregar", "todos os critérios cumpridos"
    res = {"ok": True, "criterios": julgados, "score": score,
           "veredicto": veredicto, "metodo": metodo, "perfil": cap.perfil,
           "motivo": motivo}
    _auditar(cfg, res, pedido)
    return res


def _auditar(cfg, res: dict, pedido: str) -> None:
    """Quadro completo no data_dir (privado) + resumo no agent.log
    (o pedido NÃO vaza no log — padrão D2)."""
    try:
        path = cfg.data_dir / "autoavaliacoes.jsonl"
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(
                {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                 "pedido_chars": len(pedido or ""), **res},
                ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass
    try:
        from . import activity
        activity.log(cfg, "autoavaliacao",
                     f"🪞 score {res['score']} · {len(res['criterios'])} "
                     f"critério(s) · {res['veredicto']} · {res['metodo']}")
    except Exception:  # noqa: BLE001
        pass


def formatar_quadro(res: dict) -> str:
    """O quadro ✅/⚠️/✖ que acompanha a entrega (auditável)."""
    if not res.get("criterios"):
        return (f"🪞 Autoavaliação: {res.get('motivo', 'sem critérios')}")
    linhas = [f"🪞 Autoavaliação — {len(res['criterios'])} critério(s) · "
              f"método {res['metodo']} · perfil {res['perfil']}"]
    for j in res["criterios"]:
        linhas.append(f"  {j['status']} {j['texto'][:100]}")
        if j.get("evidencia"):
            linhas.append(f"      ↳ {j['evidencia'][:140]}")
    linhas.append(f"  VEREDICTO: {res['veredicto'].upper()} "
                  f"(score {res['score']}%) — {res['motivo']}")
    return "\n".join(linhas)
