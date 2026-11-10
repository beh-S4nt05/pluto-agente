# 🗺️ MAPA DE FLUXOS V9 — PLUTO, O SECRETÁRIO

**Mapa-mestre dos fluxos do agente — nenhum fluxo fora daqui.**
Cada fluxo mostra (a) o que **JÁ existe** na v8.6.0, aterrissado em
arquivo/mecanismo real (auditoria 07/11/2026, tree `e95f401`, 241 testes,
215 arquivos no zip), e (b) o que a **V9 adiciona**, marcado por fase
`[P0]–[P7]`. Companheiros: `ROADMAP-V9-SECRETARIO.md` (fases em detalhe)
e `ROADMAP-PLUTO.md` (histórico). Este mapa responde: *por onde passa um
pedido, um token, um dado pessoal, um commit* — sem perder nada de vista.

---

## 1. MACRO-FLUXO — ciclo de vida de um pedido (O PIPELINE DO PROCESSO)

```
 Telegram ─┐                       ┌─ [2] INTERPRETAR ─── skill pedido-fiel [P5]
 WhatsApp ─┤                       │    9 dimensões · ≤3 perguntas · eco do pedido
 GUI web ──┼─► [1] ENTRADA ──────► │        │ incerto? → pergunta ao operador
 TUI chat ─┤    (5 canais)         │        ▼
 CLI ──────┘                       └─ [3] PLANEJAR ───── skill pedido-para-plano [P5]
                                          │      pedido → PRD → plano → tarefas
                                          ▼
                                   [4] REGISTRAR ────── checkpoint da tarefa [P1 ✔]
                                          │      <data>/tasks/state/<id>.json + diário
                                          ▼
                                   [5] EXECUTAR ─────── 34 tools · 50 skills
                                          │      RAG notebook (TF-IDF) · MCP externo
                                          │      ctx ≥55% → compacta [P1: +checkpoint]
                                          ▼
[6] VERIFICAR ────── 2ª passada [P2 ✔]
                                          │      cada afirmação ✓/✗/~ + confiança 0–100
                                          ▼
                                   [7] AUTOAVALIAR ──── quadro ✅/⚠️/✖ [P3]
                                          │      critérios extraídos DO PEDIDO
                                          ▼
                                   [8] DECIDIR ──────── tudo ✅ → entrega
                                          │      ✖ → corrige (volta a [5])
                                          │      incerto+destrutivo → PERGUNTA [P2]
                                          ▼
                                   [9] ENTREGAR+APRENDER
                                          resposta + quadro + confiança
                                          diário fecha [P1] · memória · skill nova
```

| # | Estágio | Hoje (v8.6.0) | V9 adiciona | Artefato persistente | Teste |
|---|---------|---------------|--------------|----------------------|-------|
| 1 | ENTRADA | TUI `pluto chat` · GUI web (`pluto/server/app.py`: `/`, `/contas`, Finanças) · Telegram (`cmd_telegram`: start/stop/chat-id/autorizar) · WhatsApp Playwright (`cmd_whatsapp`) · CLI | [P4] briefing diário entra pelo Telegram · [P8 ✔] conversas ORGANIZADAS EM NODES de projeto (`projetos.py`) | conversa em `conversations.py` (global) ou no node `projetos/<slug>/conversas/` | T253 ✔ |
| 2 | INTERPRETAR | 50 skills com gatilhos PT-BR score ≥2 (`skills.py`) · `perguntas.py` | [P5 ✔] skills **pedido-fiel** (eco + 9 dimensões + ≤3 perguntas) e **interrogar** (grill, nivel rapido) | — | T250 ✔ |
| 3 | PLANEJAR | flag `planejamento_verificado` — gate do plano estrutural+goldfish (POLITICAS.md) | [P5 ✔] skills **escrever-pedido** (PRD) + **pedido-para-plano** (plano→checkpoint) | plano no checkpoint | T250 ✔ |
| 4 | REGISTRAR | — (nada por tarefa) | [P1 ✔ ENTREGUE] **checkpoint** `tasks/state/<id>.json` (atômico, merge, critérios) + **diário** + tool `tarefa_checkpoint` (35ª) | `tasks/state/*.json` + `diario.jsonl` | T243–T244 ✔ |
| 5 | EXECUTAR | 34 tools (`tools.py`, `autoavaliar` na 34ª) · MCP 3 transportes (`mcp_client.py`) c/ seleção TF-IDF (`agent.py` L176) · RAG TF-IDF (`knowledge.py`, `notebook.py`) · orçamentos e flags POLITICAS (18) | [P6] sandbox bwrap · [P7] portões de capacidade | backups automáticos (`backups.py`) | T248 |
| 6 | VERIFICAR | `revisar.py` · `arena.py` · `certeza.py` (fluxos específicos) | [P2 ✔ ENTREGUE] **2ª passada universal** (`verificacao.py` + tool `verificar_resposta` 36ª): ✓/✗/~ por afirmação + confiança + destrutiva→perguntar | `verificacoes.jsonl` | T245 ✔ |
| 7 | AUTOAVALIAR | ~~`autonomy.pre_entrega_varredura` (só segredos)~~ | [P3 ✔ ENTREGUE] **quadro ✅/⚠️/✖** (`autoavaliacao.py` + tool `autoavaliar`) contra critérios extraídos do pedido, com evidência e veredicto | `autoavaliacoes.jsonl` | T246 ✔ |
| 8 | DECIDIR | `confirm_dangerous` (POLITICAS) · níveis cauteloso/padrao/autonomo (`contratos.py`) | [P2 ✔] incerto+destrutivo → perguntar (regra dura implementada) · [P7 ✔] aval para escalada | decisão no diário | T245/T249 ✔ |
| 9 | ENTREGAR+APRENDER | memória de fatos (`memory.py`) · rascunhos c/ aprovação (`learning.py`) · backups | [P1] fecha diário · [P3] entrega anexa quadro+confiança | memória + diário | T243–T246 |

**A regra do macro-fluxo:** nenhuma entrega pula [6] e [7] — verificar e
autoavaliar são arquitetura, não opção (Princípio 0: o perfil do cérebro
muda a *profundidade*, nunca a existência do estágio). **P8.1 (T254): a
regra é IMPOSTA pelo run_pipeline** — rodapé de verificação + quadro
anexados à entrega de task, checkpoint task-<tid> criado/fechado pelo
pipeline (correção do achado A1 da auditoria SDD; antes era só spec).

---

## 2. FLUXO DE CONTEXTO — "sem perder nada de vista"

```
num_ctx 8192 (POLITICAS.md L37: "use 8192 p/ modelos pequenos")
   │
   ├─ por resposta: msgs > 55% do ctx → _compactar()  (agent.py L364,
   │   limite = num_ctx×55//100, piso 800; chamado em L501)
   ├─ entre sessões: _RESUMED (pluto/server/app.py) recoloca os GOALS
   ├─ longo prazo: memória de fatos (memory.py) + conversas buscam
   │   indexadas (conversations.py)
   └─ conhecimento: notebook/materiais indexados por TF-IDF (knowledge.py)
```

**V9 [P1 ✔ ENTREGUE] fechou os buracos:**
- **checkpoint por tarefa** (`<data>/tasks/state/<id>.json`): objetivo,
  plano, estado das tools, parciais — a tarefa sobrevive a compactação,
  restart e truncamento;
- **alerta de truncamento**: quando o modelo corta resposta
  (finish_reason ou texto sem fecho), o agente detecta, anota no
  checkpoint e retoma de onde parou — em vez de entregar metade;
- **diário de trabalho**: 1 linha por estágio do macro-fluxo — o
  operador audita o que o secretário fez no dia.

---

## 3. FLUXO DE CAPACIDADE — Princípio 0 (o modelo é a BASE, não o limitador)

```
config (config.py + config.example.yaml)
   │  provedor ativo: Ollama local OU 1 dos 8 grátis do REGISTRY
   │  (llm_providers.py L29) — pluto provider set/test/off/arena
   ▼
capacidades(cfg)  [P7 ✔ ENTREGUE — pluto/capacidades.py]
   │  cerebro_ativo(): provider fixado > roteador automático
   │  (chave guardada) > Ollama local — a MESMA decisão do agente
   │  PERFIL: leve | rapido | forte (tamanho no nome / padrões)
   │  PORTÕES: verificacao_completa · skills_avancadas · ctx_longo ·
   │  computer_use · autonomia_estendida — cap.aberto(portão)
   │  override: capacidades_perfil no config.yaml
   ▼
 consultantes: catálogo de skills (JÁ filtra por nivel ✔) ·
 verificação [P2] · autoavaliação [P3] · escalonamento (solicitar_
 escalada ✔ pronto; entrega no Telegram na P4)
```

**Invariante:** nenhum módulo pergunta "que modelo é?" — todos consultam
os portões. Trocar o cérebro no config muda o comportamento no próximo
boot, **sem refatorar** (provado pelo teste T249 com dois perfis).

---

## 4. FLUXO DE ESCALONAMENTO DE CÉREBRO [P7]

```
tarefa crítica/complexa chega em [5] EXECUTAR
   → supervisor avalia: perfil atual = leve? cérebro forte disponível
     no REGISTRY com quota? valer a pena?
   → pede AVAL ao operador (Telegram) — nunca silencioso
   → aprovado: executa no forte · gasta quota só nesta tarefa
   → recusado/sem resposta: segue no leve com verificação [P2]
```

Hoje a troca é manual (`pluto provider set` + `pluto arena` para
comparar). A V9 torna o roteiro por tarefa, com política de gasto em
POLITICAS.md.

---

## 5. FLUXO CI/CD — o pipeline que guarda o pipeline [P0 = T242]

```
LOCAL                         GITHUB                          LOCAL
─────                         ──────                          ─────
pluto gates ─────►  push p/ main ─► CI (ci.yml):       ─► tag v* ─► Release (release.yml):
(1 comando,                │         1 ruff check                │      rerefaz os 3 portões
 3 portões:                │         2 suíte run_all.py          │      git archive → zip
 1 ruff                    │           matriz: ubuntu            │      gh release create
 2 suíte                   │           windows macos             │      (Release no GitHub c/ zip)
 3 varredura)              │         3 pluto varredura --tudo    └─► pós-tag local: suíte de novo
                           │         (PYTHONUTF8=1: PT-BR não
                           │          morre no console Windows)
                           ▼
                    PR: mesmos portões antes do merge
```

- **Hoje (pré-P0):** 103 tags liberadas com gates 100% manuais —
  disciplina que funcionou, mas não escala e não protege o repo de
  terceiros. `.github/workflows/` inexistente.
- **P0 ENTREGUE (07/11/2026, run 42343666440 = SUCCESS nos 3 SOs):**
  `ci.yml` (push/PR → matriz Linux|Windows|macOS → ruff + suíte +
  varredura), `release.yml` (tag `v*` → portões completos →
  `git archive` zip idêntico ao processo local → GitHub Release), e
  `pluto gates` local — **o espelho exato do CI em 1 comando**.
  Nas 3 primeiras rodadas o pipeline já pegou: 43 testes POSIX-only
  (dívida rastreada em `docs/PORTABILIDADE.md`, pulada CONTADA nos
  jobs win/mac) e 1 bug real de determinismo no arena (corrigido).
- **Invariante do zip:** só arquivos rastreados (`git ls-files`) —
  dados pessoais nunca entram (ver §6).

---

## 6. FLUXO DE DADOS PESSOAIS & SEGURANÇA

```
DADOS (vault, ~/.pluto, notebook, memória)     CÓDIGO (repo GitHub)
─────────────────────────────                  ─────────────────────
· NUNCA no repo: data_dir é                    · varredura.py: varre diff
  fora (Config(data_dir=...))                    e repo rastreado; padrões
· backups.py: cópia antes de                    como ghp_[A-Za-z0-9]{30,}
  reescrever                                     → CRITICO bloqueia push
· POLITICAS.md: 18 flags —                      · falso positivo intencional:
  confirm_dangerous · planejamento_               marca '# varredura:ok'
  verificado · sandbox (bwrap+seccomp             na linha
  "quando disponível") · orçamentos             · autonomy.pre_entrega_varredura:
· zip de release = git archive                   última varredura ANTES de
  (só rastreados = só código)                    expor código
```

**V9 [P6 ✔ ENTREGUE]:** a camada de kernel é da v4.0.0
(`sandbox_kernel.py`: bwrap+seccomp no `run_command`); a P6 fechou o
que faltava: tool `git` também enjaulada (net=False — operação local
não precisa de rede) e **prova REAL no CI** (bwrap instalado no runner
Linux + T251 executando a jaula a cada push: fora→falha, dentro→ok,
net off→sem socket). trycua/cua segue como referência do portão
`computer_use`. Bug T107 (denylist × symlink) → P0.1.

---

## 7. FLUXOS DE SECRETARIADO [P4 = T247–T248]

| Fluxo | Hoje | V9 |
|-------|------|-----|
| **Briefing diário** | — | ✔ P4: `secretario.tick` (Scheduler, 15 s) dispara na `briefing_hora`: agenda + e-mails triados + tarefas ativas (checkpoints) + diário de ontem → **Telegram** |
| **Lembretes** | Calendar com ESCRITA (escopo `calendar.events`, `agenda_criar`, fuso da máquina) | ✔ P4: `lembrete_min` (30) antes → Telegram, 1×/dia por evento (`eventos_estruturados`) |
| **Triagem de e-mail** | `emailcfg.py` (Gmail/Microsoft OAuth) conectado | ✔ P4: `triar_emails` IMAP (XOAUTH2/senha) — "precisa de você" × informativo, resumo no briefing |
| **9 vinculações** | página `/contas` (Google Calendar, Gmail/Microsoft, Telegram, WhatsApp, SumUp, Belvo, 8 provedores IA, n8n, vault) com status honesto e teste real | idem — base pronta |

---

## 8. FLUXO MCP — ferramentas externas

```
config mcpServers: [{name, url|command, transport: stdio|streamable|sse}]
   → get_manager() (manager.py)
   → openai_tools(): mcp_<servidor>_<tool> · mcp_recurso · mcp_prompt
   → _select_mcp_tools(query)  (agent.py L176): TF-IDF top-k —
     só as tools relevantes à query entram no prompt (ctx 8192)
   → chamada: stdio | Streamable HTTP | SSE clássico (SSEServer:
     GET stream → event: endpoint → POST → resposta por id)
   → falha: MCPError honesto (porta morta) · degradação honesta
     (sem resources → [])
```

[P7] portão `computer_use`: integração cua via MCP documentada e
desligada até o perfil suportar — ligar não exige reescrita
(fundação pronta: jaula provada no CI — T251).

---

## 9. FLUXO DE SUPERVISÃO & RECUPERAÇÃO DE FALHAS

```
servidor MCP morre → McpSupervisor (supervisor.py):
   restart com backoff 60×2^(n-1) s, teto 600 s (BACKOFF_CAP_S)
diagnóstico → doctor.py · boot.py
serviço SO  → daemon.py (pluto-agent.service, systemd/)
agente      → backups.py (tudo que reescreve, copia antes)
```

[P1] adiciona a camada que falta: a **tarefa** também sobrevive
(checkpoint), não apenas o processo.

---

## 10. MATRIZ DE RASTREABILIDADE — requisito → fase → mecanismo → teste

| Requisito do operador | Fase | Mecanismo | Teste | Status |
|---|---|---|---|---|
| "pipelines CI/CD para código" | **P0** | ci.yml + release.yml + `pluto gates` | **T242** | ✅ entregue (3 SOs verdes) |
| "o modelo não é o limitador" | **P7** | `capacidades(cfg)` perfis+portões | T249 | ✅ entregue (DoD-7 provado) |
| "autoavaliação: dentro do pedido? entrega correta?" | **P3** | quadro ✅/⚠️/✖ auditável | T246 | ✅ entregue (tool `autoavaliar`) |
| "autonomia sem perder contexto" | **P1** | checkpoint + alerta truncamento + diário | T243–T244 | ✅ entregue (bug de empate pego pelo CI e corrigido) |
| "sem alucinações demasiadas" | **P2** | 2ª passada ✓/✗/~ + confiança + perguntar | T245 | ✅ entregue (36 tools) |
| "me dando tempo" (proatividade) | **P4** | briefing diário + lembretes + triagem | T247–T248 | ✅ entregue (opt-in no config) |
| skills externas validadas | **P5** | 5 skills PT-BR graduadas por nível | T250 | ✅ entregue (55 skills, auditoria limpa) |
| execução isolada | **P6** | bwrap+seccomp por padrão | T248 | ⏳ |

---

## 11. STATUS POR FLUXO (hoje → V9)

| Fluxo | v8.6.0 | V9 |
|-------|--------|-----|
| Macro-fluxo do pedido | estágios 1,3,5,8,9 fortes · 2 razoável · 4,6,7 ausentes | **desenho V9 completo**: 4·6·7 ✔ (P1·P2·P3) + skills de 2·3·7 ✔ (P5) |
| Contexto | compacta/resume/memória | + checkpoint, truncamento, diário — **✔ P1** |
| Capacidade | fixa no config | perfis + portões + escalonamento — **✔ P7** (pluto capacidades) |
| CI/CD | manual (103 tags) | Actions 3 SOs + release automática + gates local — **LIVE ✔** (dívida: 43 testes win/mac em docs/PORTABILIDADE.md) |
| Dados/segurança | varredura + 18 flags + backups | + bwrap padrão |
| Secretariado | canais + agenda + 9 vinculações | + briefing, lembretes, triagem — **✔ P4** (`pluto secretario`) |
| MCP | 3 transportes + paridade Genkit | + portão computer_use |
| Supervisão | supervisor + doctor + daemon | + checkpoint de tarefa |

*MAPA-FLUXOS-V9.md · 07/11/2026 · fonte: auditoria v8.6.0 · mantido
em sincronia com o ROADMAP-V9-SECRETARIO.md — mudou o fluxo, muda o mapa.*
