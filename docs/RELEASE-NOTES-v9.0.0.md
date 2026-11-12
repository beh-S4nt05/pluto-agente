# Pluto Agente v9.0.0 — 🤵 O Secretário

A versão do **"agente que cuida de você"**. Local-first (Ollama +
hermes3), com roteador opcional de provedores grátis — código e
segredos nunca saem (D2). Windows · macOS · Linux (x86-64 e ARM64).

## O que mudou (desde a v8.6.0)

- **CI/CD de verdade**: 3 SOs · 4 portões (ruff → suíte → varredura
  de segredos → **cobertura ≥66%**) · release publicada sozinha a
  partir da tag, com zip (`git archive`, só arquivos rastreados).
- **Cérebro escalável (Princípio 0)**: `capacidades.py` — o perfil do
  cérebro ATIVO abre portões (verificação completa, skills avançadas,
  contexto longo, computer-use). **Trocar de cérebro no config muda o
  comportamento sem mexer em código** (T249).
- **Anti-alucinação imposta**: 2ª passada com verificações ✓/✗/~ e
  confiança; destrutiva + baixa confiança → pergunta ao operador;
  quadro de autoavaliação contra o pedido em toda entrega (T245–T246).
- **Contexto durável**: checkpoint por tarefa, diário, `retomar()`
  sem reler o chat (T243–T244).
- **Secretário proativo** (opt-in): briefing diário no Telegram,
  lembretes, triagem de e-mail (T247–T248).
- **Projetos como nodes**: cada projeto é um grupo de conversas com
  contexto e artefatos próprios; tool `projeto` (37ª) + `/api/chat`
  (T253).
- **Sandbox provado no CI**: bwrap de kernel no Linux do runner —
  escrever fora falha, rede off não conecta (T251).
- **Segurança (auditorias externas nº 1 e nº 2)**: estágios de
  verificação IMPOSTOS no pipeline · `git_run` com denylist na tool ·
  DLP no secretário · segredos por data-dir · **21 rotas de API que
  burlavam a auth agora exigem token** (incluindo a que move dinheiro)
  · inventário do `url_map` trava rota nova sem classificação (T262).
- **Portabilidade: dívida ZERO**: 262/262 testes, **0 pulados nos 3
  SOs** (eram 38 no Windows · 5 no macOS em 07/11).

## Status honesto (Diretriz 7 — sem sucesso fingido)

- **Aberto (campo do operador)**: DoD#6 — 1 dia de uso real com
  Ollama local de pé. Harness pronto: `pluto selftest` (bateria com
  LLM real; pula limpo sem Ollama).
- **Backlog declarado**: cobertura 75→82→89% (plano F1–F3 em
  `docs/VALIDACAO-PONTO-A-PONTO-V9.md` §5) · ACL/keyring no Windows ·
  P0.2 (saída web/e-mail/MCP não confiável — §4 da auditoria nº 2).

## Instalação

```
pip install pluto-agente    # ou: pip install -e . a partir do zip
pluto setup                 # GUI de configuração completa
pluto up                    # liga o servidor (GUI :8080)
```

Suíte: `python tests/run_all.py` (262 casos) · Especificação:
`SPEC.md` · Histórico completo: `CHANGELOG.md`.
