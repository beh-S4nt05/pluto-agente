# 📐 SPEC — Pluto Agente · Especificação-Mestre (SDD)

> **Spec-Driven Development**: este documento é a fonte da verdade do
> produto. A regra de ouro do processo é **testar antes de criar,
> validar antes de melhorar** — e a regra deste documento é: *mudou o
> comportamento, muda a spec junto no MESMO commit*.
>
> Escrito em 09/11/2026, no meio do desenvolvimento da **v9.0.0**
> (P0–P8 entregues; P0.1 pendente → release). Status de verificação de
> cada item é DECLARADO (Diretriz 7: sucesso só com prova; "não
> verificado" é estado válido, sucesso fingido não).
>
> Operador: **Breno** · Repo: `beh-S4nt05/pluto-agente` (main) ·
> Suíte: **261 casos** · Tools: **37** · Skills: **55** · CI: **3 SOs**
> (ubuntu · macos · windows) — último verde: ver §8.

---

## 1. Visão e identidade

**Pluto Agente** é um agente de IA **local-first** para a máquina do
operador: diagnosticar, gerenciar e automatizar — por terminal (CLI/TUI),
interface web (GUI/PWA), Telegram e WhatsApp. Fala **português do
Brasil** por padrão. O modelo (cérebro) roda no **Ollama local** e pode
escalar para provedores externos gratuitos **sem que código, segredos ou
dados pessoais saiam da máquina** (D2).

- **Cadeia de nomes** (mesmo produto): `hermes` (v1–v3) → `betterme`
  (v4.1.0) → **`pluto`** (v8.3.0 — nome final). O REPOSITÓRIO de
  desenvolvimento mantém o nome `hermes-agent`; o pacote instalável é
  `pluto` (nome antigo só em comentários de compatibilidade do `update.py`).
- **Zero dependência pesada**: Python stdlib onde dá; o que é externo
  (Ollama, whisper.cpp, n8n, Playwright) é opcional e degrada com
  honestidade.
- **Nativo de verdade**: nada de "instruir o usuário a fazer" — o agente
  FAZ (nota fiscal, OCR, notebook, transcrição, finanças).

---

## 2. Bases de desenvolvimento (invioláveis)

### 2.1 Princípio 0 — o modelo é a base, nunca o limitador

O cérebro é recurso calibrável, não teto do produto (diretiva do
operador, 07/11/2026):

1. **Model-agnostic**: trocar o cérebro no config não exige refatoração.
2. **Portões de capacidade** (`capacidades.py`, P7): cada funcionalidade
   exigente declara um portão; cérebro fraco = profundidade menor,
   **nunca recusa** — skills graduadas por nível, verificação sempre
   presente (leve = checklist; rápido = completa; forte = re-checagem
   cruzada).
3. **hermes3:8b é o piso** de teste: se funciona no piso, funciona.
4. **Auto-escalonamento só com aval do operador** — nunca silencioso.
5. Prova viva: T249 troca o perfil do cérebro e verifica
   capacidades/portões mudarem SEM tocar em código.

### 2.2 Decisões D1–D5 e ADR-001 (v4.0.0 — "decisões do operador viram lei")

- **D2 (`payload_sensivel`)**: código/segredo detectado no pedido →
  cérebro LOCAL, sempre. Todo payload que vai a provedor externo passa
  por `mascarar()` (DLP): segredos/CPF/e-mail → `[REDACTED]`. **Código
  nunca sai da máquina.**
- **D5**: gerente de código (Claude Code) é **opt-in consciente**, com
  aviso de privacidade explícito antes de ligar.
- **ADR-001**: o agente é **1 cérebro main + especialistas-como-
  ferramentas** (veredito JSON com evidência validada em disco), não
  "1 cérebro + skills" solto.
- D1–D5 completas: CHANGELOG v4.0.0 + `POLITICAS.md` (regras de lei:
  denylist, secrets, D2, escopo).

### 2.3 Diretrizes do operador (modo de trabalho — `DIRETRIZES.md`)

1. **"Faça" = executa** (sem explicar antes; confirmar depois).
2. **Relatório/revisão = caçar problemas** (achados acionáveis).
3. **"Explique" = ensinar** (só quando pedido).
4. **README sempre em dia** em toda release (nunca versões atrás).
5. **Antes de perguntar ou duvidar: CONSULTE primeiro** — (1º) contextos
   e bases da conversa; (2º) processo em trabalho; (3º) só então
   perguntar.
6. **Honestidade radical — sucesso só com prova** (09/11/2026, após o
   P6): obrigatória para **qualquer ser humano** com quem se trabalhe.
   Nunca apresentar como feito/provado o que não foi provado DE VERDADE;
   "verde" não substitui verificação; o caminho que rodou fica VISÍVEL;
   "não verificado" é declarado. **Gravada no cerne do agente**
   (SYSTEM_PROMPT) e garantida pelo T252 no CI dos 3 SOs. (Numeração
   corrigida em 10/11/2026 — era "Diretriz 7"; fonte versionada em
   `docs/DIRETRIZES.md`.)

### 2.4 Regras que não mudam (roadmap §6)

Local-first · D2 (código/segredos nunca saem) · dados pessoais fora do
repo · PT-BR · suíte 100% + ruff + varredura antes de tag · achado de
campo vira regressão · honestidade antes de promessa · testar antes de
criar · validar de verdade.

### 2.5 Políticas de qualidade e processo

| Política | Valor |
|---|---|
| SOs suportados | Linux · macOS · Windows (x86-64 e ARM64); Python ≥3.9 (análise estática), CI cobre 3.11 e 3.13 (P8.3) |
| Suíte de regressão | 253 casos (`tests/run_all.py`), auto-descoberta `@case` |
| Gates de CI | ruff (`E9,F,B,PLE`) → suíte → varredura de segredos |
| Performance | resposta >50 s inaceitável (orçamentos em POLITICAS.md) |
| Orçamento do system prompt | **<6000 chars** (T12; T252 imprime `N/6000` no log do CI) |
| Pré-tag | suíte + ruff + varredura + `CHECKLIST-PRE-RELEASE.md` |
| Pré-push | varredura de segredos (CRÍTICO bloqueia) — via hook git: `pluto gates --instalar-hook` (P8.2) |
| Ensino | CBTA (IS 141-007), teor ≥75% (v7.7.0) |
| Segredos | arquivos chmod 600 no data-dir; **token GitHub nunca no repo** |
| Commits | granulares, mensagem = raciocínio + lição (por que, não só o quê) |
| Versão | major por marco (exceto quando o operador escolhe minor) |

---

## 3. Arquitetura

```
                    ┌───────────── CANAIS DE ENTRADA/SAÍDA ─────────────┐
                    │ TUI (chat) · GUI web Flask (PWA) · CLI · Telegram │
                    │ · WhatsApp (Playwright) · e-mail · scheduler       │
                    └───────────────────────┬───────────────────────────┘
                                            │
                    ┌───────────────────────▼───────────────────────────┐
                    │ ORQUESTRADOR (orchestrator.py · fluxos 3 níveis)  │
                    │ pipeline: interpretar → planejar → executar →     │
                    │ verificar (P2) → autoavaliar (P3) → entregar      │
                    └───────────────────────┬───────────────────────────┘
                                            │
      ┌─────────────────────────────────────▼──────────────────────────────┐
      │ AGENTE (agent.py): system prompt orçado · cache de prompt · anti-  │
      │ loop · fallback JSON · 37 TOOLS · MCP · skills · memória · RAG     │
      └──────┬──────────────────────┬──────────────────────┬───────────────┘
             │                      │                      │
   ┌─────────▼─────────┐  ┌────────▼─────────┐  ┌─────────▼─────────────┐
   │ CÉREBRO           │  │ CONTEXTO         │  │ EXECUÇÃO              │
   │ Ollama local      │  │ conversas        │  │ sandbox de kernel     │
   │ provedores grátis │  │ memória de fatos │  │ (bwrap+seccomp)       │
   │ omniroute/arena   │  │ checkpoints/diário│ │ git enjaulado (P6)    │
   │ capacidades (P7)  │  │ projetos/nodes(P8)│ │ grafo AST · revisar   │
   └───────────────────┘  └──────────────────┘  └───────────────────────┘
```

Inventário de módulos (~80 em `pluto/`) — mapa completo em
`MAPA_APLICACAO.md`. Domínios: cérebro (`ollama_client`,
`llm_providers`, `omniroute`, `arena`, `autoselect`, `capacidades`,
`claude_agent`) · núcleo (`agent`, `orchestrator`, `fluxos`, `comandos`,
`gateway`, `boot`, `daemon`, `cli`, `tui`, `server/`) · ferramentas
(`tools`, `sandbox_kernel`, `grafo`) · memória/contexto (`memory`,
`contexto`, `conversations`, `projetos`, `knowledge`, `notebook`,
`project_context`, `vault`, `learning`) · qualidade (`verificacao`,
`autoavaliacao`, `revisar`, `selftest`, `doctor`, `varredura`, `audit`,
`metrics`, `supervisor`) · canais (`telegram_gw`, `whatsapp_gw`,
`emailcfg`, `notify`, `stt`, `multimodal`, `ocr`) · finanças
(`financas`, `contas`, `belvo`) · integração (`mcp_client`, `manager`) ·
SO (`plataforma` — único lugar onde Unix-ismos vivem).

---

## 4. Macro-fluxo do pedido (9 estágios — MAPA-FLUXOS-V9.md)

| # | Estágio | O que roda | Artefato persistente |
|---|---------|-----------|----------------------|
| 1 | ENTRADA | TUI · GUI · Telegram · WhatsApp · CLI · briefing (P4) | conversa (`conversations.py`) |
| 2 | INTERPRETAR | 55 skills c/ gatilhos PT-BR · pedido-fiel (P5) | — |
| 3 | PLANEJAR | gate `planejamento_verificado` · escrever-pedido/pedido-para-plano (P5) | plano no checkpoint |
| 4 | REGISTRAR | checkpoint `tasks/state/<id>.json` + diário (P1) | `tasks/state/*.json` + `diario.jsonl` |
| 5 | EXECUTAR | 37 tools · MCP 3 transportes · RAG · sandbox (P6) · portões (P7) | backups automáticos |
| 6 | VERIFICAR | **2ª passada universal** ✓/✗/~ + confiança (P2) | `verificacoes.jsonl` |
| 7 | AUTOAVALIAR | quadro ✅/⚠️/✖ contra o pedido (P3) | `autoavaliacoes.jsonl` |
| 8 | DECIDIR | confirm_dangerous · autonomia 3 níveis · incerto+destrutivo→perguntar | decisão no diário |
| 9 | ENTREGAR+APRENDER | memória · rascunhos c/ aprovação · quadro+confiança anexos | memória + diário |

**Regra do macro-fluxo**: nenhum entrega pula [6] e [7] — verificar e
autoavaliar são **arquitetura**, não opção. O perfil do cérebro muda a
*profundidade*, nunca a existência do estágio. **P8.1 (T254)**: a regra
é IMPOSTA pelo `run_pipeline` — toda entrega de TASK sai com o rodapé
de verificação (✓/✗/~ + confiança) e o quadro de autoavaliação
anexados pelo pipeline, e o checkpoint `task-<tid>` é criado no início
e fechado no fim; conversa (fast lane) segue leve. (Correção do achado
A1 da auditoria SDD: antes a regra vivia só nesta spec.)

---

## 5. Requisitos funcionais por domínio

### 5.1 Cérebro escalável (Princípio 0 como mecanismo)

- **RF-CER-01** Ollama local é o cérebro padrão; falha de servidor é
  mensagem honesta com instrução de recuperação (nunca silêncio).
- **RF-CER-02** Provedores externos gratuitos (groq/gemini/mistral/
  openrouter/llm7/zai/cohere) via registro OpenAI-compat; chave em
  secrets 600; **memória nunca sai** (v3.17.0, regra do operador).
- **RF-CER-03** Roteador automático (v6.3.0): escolhe o cérebro por
  tarefa, com D2 no transporte (pedido mascarado, v6.4.2).
- **RF-CER-04** Arena (v4.3.0): a MESMA task em todos os contendores
  do pool grátis, cronometrada, revisor local ranqueia.
- **RF-CER-05** Capacidades (P7·T249): `PORTOES` + `NIVEIS_SKILL` +
  `capacidades_perfil` — o perfil do cérebro ativo define portões
  abertos e skills visíveis; trocar cérebro = trocar perfil SEM código.
  *Portões RESERVADOS (computados, ainda sem consumidor — declarado
  honestamente):* `ctx_longo` · `autonomia_estendida` · `computer_use`
  (fundação pronta: jaula provada no CI — P6). Auto-escalonamento com
  aval do operador: **backlog** — a função morta `solicitar_escalada`
  foi removida na P8.3 (auditoria M9); trocar de cérebro hoje é manual
  (`pluto provider set` / config), nunca silencioso.
- **Verificação**: T249 (2 perfis) · T127 (modelo do provedor).

### 5.2 Ferramentas e execução

- **RF-EXE-01** 37 tools nativas (`tools.py`): diagnóstico, arquivos,
  processos (start/logs/stop), edit_file, perguntar_operador,
  lembrar/esquecer, web (search/fetch), git enjaulado, grafo_query,
  revisar_diff, verificar_resposta (36ª), projeto (37ª)…
- **RF-EXE-02** Sandbox de kernel (v4.0.0): bwrap `--ro-bind / /` +
  `--dev` + `--proc`, workspace `--bind` rw, `--unshare-net` opcional;
  seccomp BPF blocklist à mão (ptrace/mount/kexec/bpf…→EPERM, filtro
  len%8==0); modos auto|kernel|app; `probe()` decide; **degradação
  honesta** sem bwrap (argv intacto, nunca quebra).
- **RF-EXE-03** Prova real no CI (P6·T251): o runner Linux instala
  bubblewrap, libera `kernel.apparmor_restrict_unprivileged_userns`
  (lição do run 42555505782) e a suíte EXECUTA a jaula: escrever FORA
  falha · DENTRO ok · net=False não conecta · BPF estruturado ·
  marcador `jaula REAL (nível X)` vs `degradação honesta` **impresso
  no log** (CI verde ≠ jaula provada; o marcador prova qual caminho
  rodou).
- **RF-EXE-04** `git_run` enjaulado com **net=False** (P6): operações
  locais (`_GIT_OK`: init/status/add/commit/log/diff/branch/checkout/
  show/tag/restore/stash/config) rodam sem rede no kernel;
  fetch/push seguem pelo `run_command` (que decide rede).
  **P8.1 (T255, auditoria A2)**: denylist NA TOOL, valendo com ou sem
  bwrap — chaves de config que EXECUTAM comandos no host
  (`core.fsmonitor`/`core.sshCommand`/`core.hooksPath`/`core.pager`/
  `core.editor`/`alias.*`…) e `--output` (escrita fora do workspace)
  são BLOQUEADOS; config comum e diff normal seguem.
- **RF-EXE-05** Comandos perigosos (raiz, formatar, desligar)
  bloqueados por denylist (POLITICAS.md). **T107 ✔ corrigido na P0.1**:
  o `_SCOPE_DENY` nega nos dois planos (caminho dado E resolvido —
  symlink de sistema não escapa mais).
- **Verificação**: T251 · T131 · T188 · T107 (aberto).

### 5.3 Memória e camadas de contexto

Nove camadas, cada uma com dono e orçamento:

| # | Camada | Onde vive | Regra |
|---|--------|-----------|-------|
| 1 | System prompt | `agent.py` | **<6000 chars** (T12), cache estável + hora fresca fora do cache; concisão e anti-alucinação no cerne |
| 2 | Catálogo de skills | `skills.py` | 18 linhas por relevância da query, graduado pelo nível do cérebro (P7) |
| 3 | Contexto de projeto | `project_context.py` | HERMES.md/AGENTS.md (global + task scope), cap 32 KiB, DLP para externo |
| 4 | Memória de fatos | `memory.py` | lembrar/esquecer; **nunca** vai a provedor externo |
| 5 | Histórico da conversa | `conversations.py` | últimas 20 mensagens no pipeline; sessões persistentes com título |
| 6 | Checkpoint de tarefa | `contexto.py` (P1) | `tasks/state/S%04d.json` atômico (tmp+replace): objetivo, critérios extraídos do pedido, plano, feitos, próximos, bloqueios; `retomar()` reconstrói sem reler o chat |
| 7 | Diário de trabalho | `contexto.py` (P1) | `diario.jsonl` — 1 linha/evento; espelho Obsidian (escopo diario); alerta de truncamento registrado (fim da perda silenciosa) |
| 8 | Contexto do node de projeto | `projetos.py` (P8) | `contexto.md` + `anotacoes.jsonl` datadas (ver 5.4) |
| 9 | RAG / biblioteca | `knowledge.py`, `notebook.py`, `multimodal.py` | TF-IDF determinístico; fontes citadas; transcrições whisper.cpp locais |

- **Verificação**: T243–T244 (P1) · T117 (compactação) · T30 (export) ·
  T253 (P8).

### 5.4 Projetos como nodes (P8 — proposta do operador, 09/11/2026)

> Semântica confirmada pelo operador: **por dentro, o node é um GRUPO
> DE CONVERSAS** — o projeto agrupa conversas (e com elas o contexto e
> os artefatos gerados).

```
Projeto → RPG
├── Conversas                    ← o grupo de conversas do projeto
├── Contextos etc                ← contexto.md + anotações datadas
└── Recursos/artefatos gerados   ← o que o agente gera p/ o projeto
```

Em disco (`<data>/projetos/<slug>/`):

```
projetos/rpg/
├── projeto.json                 metadados (nome, descrição, status,
│                                criado_em/atualizado_em — atômico)
├── conversas/sessions/*.json    ConversationStore ESCOPADO ao node
│   └── current.json             ponteiro DO node (não polui o global)
├── contexto/
│   ├── contexto.md              contexto vivo (editável)
│   └── anotacoes.jsonl          anotações datadas (append-only)
└── artefatos/                   recursos gerados (nome validado
                                 contra travessia de diretório)
```

- **RF-PRJ-01** Slug seguro: nome → `a-z0-9-` sem acento, máx 40;
  `../../etc/passwd` → `etc-passwd` (sem travessia).
- **RF-PRJ-02** CRUD do node: `criar` (duplicata e nome inválido →
  erro honesto), `arquivar`/`reativar` (status), `obter`/`listar`
  (contagens vivas: n_conversas · n_anotacoes · n_artefatos).
- **RF-PRJ-03** Conversas do node: mesmas sessões do
  `ConversationStore`, por baixo do node; a sessão carrega
  `projeto: <slug>` (origem); **isolamento duplo** provado: nada do
  node aparece no escopo global e vice-versa.
- **RF-PRJ-04** Contexto do node: `anotar` (append datado) e
  `contexto` (lê contexto.md + últimas 10 anotações).
- **RF-PRJ-05** Artefatos: `artefato` (projeto, nome, conteudo) salva
  DENTRO do node; `../`, `a/b`, vazio, `.` → erro.
- **RF-PRJ-06** Tool 37ª `projeto`: ações `arvore|criar|anotar|
  contexto|artefato|arquivar|reativar`; `arvore` sem projeto lista os
  nodes, com projeto desenha a árvore com contagens.
- **RF-PRJ-07** CLI `pluto projeto <acao> [nome] [texto…]` (mesmas
  ações; artefato é do agente — no CLI o operador edita o arquivo).
- **RF-PRJ-08** `/api/chat` aceita `"projeto"`: a conversa NASCE no
  node; projeto inexistente → **400 explícito** com instrução de
  criação (nunca silêncio).
- **Verificação**: T253 (11 blocos: slug/travessia, CRUD, contexto,
  artefatos, árvore, isolamento, status, tool, server, CLI).

### 5.5 Skills (55)

- **RF-SKL-01** Formato SKILL.md PT-BR <8192 bytes, gatilhos com
  flexões, importação de pasta, zip, git, owner/repo; scan de pastas
  assistidas; auditoria. **Escopo do `## Exemplo` e do `nivel`
  (P8.3, auditoria M8): OBRIGATÓRIOS nas skills V9 (P5 — 6/6 têm);
  RECOMENDADOS nas legadas — a auditoria reporta a contagem sem
  reprovar; `nivel` é opt-in (padrão leve = visível em todos os
  perfis; a graduação existe e as skills V9 a exercitam).
- **RF-SKL-02** Graduação (P7): skill avançada não entra no prompt de
  cérebro leve — continua instalada/inventariada, só não é sugerida.
- **RF-SKL-03** Skills V9 do pedido (P5·T250): **pedido-fiel** (eco
  literal do pedido + 9 dimensões + ≤3 perguntas + suposição
  declarada) · **escrever-pedido** (PRD DEVE/MELHOR TER/NÃO FAZER) ·
  **pedido-para-plano** (plano → tarefa_checkpoint) · **interrogar**
  (≤5 perguntas com porquê+opções, nível rapido) ·
  **autoavaliar-entrega** (ritual: verificar → autoavaliar →
  checkpoint/fechar → rodapé).
- **RF-SKL-04** Loop de aprendizado: rascunhos em staging, aprovação
  do operador, nada entra no catálogo sem aval.
- **Verificação**: T250 · auditoria de 55 skills limpa.

### 5.6 Verificação e autoavaliação (anti-alucinação — arquitetura)

- **RF-VER-01** 2ª passada universal (P2·T245): cada afirmação factual
  da resposta é conferida contra os DADOS das tools — ✓ lastreada ·
  ✗ sem lastro · ~ incerta (declarar); score de confiança no rodapé;
  veredicto `entregar|corrigir|declarar-incertezas|perguntar-operador`.
  **P8.1 (T254): IMPOSTA pelo run_pipeline** — o rodapé é anexado à
  entrega de TASK com os dados reais colhidos dos eventos `tool_end`
  (não depende do modelo escolher a tool).
- **RF-VER-02** Regra dura: **destrutiva + ✗ (ou confiança <80) →
  perguntar_operador** (nunca executar às cegas).
- **RF-VER-03** Juiz opcional pelo cérebro (mesmo contrato, JSON
  torto → fallback heurística determinística).
- **RF-VER-04** Auditoria: `verificacoes.jsonl` + linha no log SEM
  vazar a resposta (D2).
- **RF-AUT-01** Autoavaliação (P3·T246): quadro ✅/⚠️/✖ contra
  critérios EXTRAÍDOS do pedido original, com evidência e veredicto;
  `autoavaliacoes.jsonl`; tool `autoavaliar` (34ª). **P8.1 (T254):
  IMPOSTA pelo run_pipeline** — o quadro acompanha toda entrega de
  TASK.
- **Verificação**: T245 · T246 · T252 (regra no cerne do prompt).

### 5.7 Secretário proativo (P4)

- **RF-SEC-01** Briefing diário no Telegram (agenda + pendências +
  e-mails), 1 mensagem, sem pedir — opt-in (`briefing_on=False`,
  `briefing_hora="07:00"`). **P8.1 (T256, auditoria A3)**: o que SAI
  pelo canal é mascarado (DLP): assunto/título/horário seguem,
  remetente/e-mail/CPF/segredo NÃO saem (`[REDACTED:…]`) — fim da
  contradição com NFR-01.
- **RF-SEC-02** Lembretes de compromissos (`lembrete_min=30` antes).
- **RF-SEC-03** Triagem de e-mail com ação sugerida
  (`email_triagem_on=False`) — opt-in consciente.
- **RF-SEC-04** Scheduler + CLI `pluto secretario status|briefing`.
- **Verificação**: T247–T248.

### 5.8 Canais

- **RF-CHA-01** GUI web (Flask): `/api/chat` NDJSON stream ·
  responsiva/PWA · log ao vivo · aba Ollama/Finanças/Contas/Fluxos.
- **RF-CHA-02** Telegram: long-polling, token 600, allowlist de
  chats, aprovação de tarefas pelo celular.
- **RF-CHA-03** WhatsApp via Playwright (grátis/local/removível,
  experimental, extra opcional).
- **RF-CHA-04** E-mail IMAP/SMTP com OAuth/XOAUTH2, somente leitura
  por padrão.
- **RF-CHA-05** Modo vida (v5.0.0): missões agendadas determinísticas
  (dispatcher ANTES do LLM — zero tokens), relatório diário, curadoria
  semanal.

### 5.9 Finanças

- **RF-FIN-01** Gestor completo (v8.4.0): controles de gastos, aba na
  GUI, contas a pagar/receber.
- **RF-FIN-02** Open Finance pela lista oficial + Belvo MCP (v7.4.0);
  PF inviável via API direta → **CSV + SumUp + hook** (decisão de
  campo).
- **RF-FIN-03** OCR nativo (v8.2.0) e notebook RAG (v8.1.0, clone
  funcional do NotebookLM) para extratos/notas.

### 5.10 MCP (paridade Genkit, v8.6.0)

- **RF-MCP-01** 3 transportes: stdio · Streamable HTTP · SSE clássico
  (implementação própria em stdlib; zero dependência nova).
- **RF-MCP-02** Ferramentas + recursos + prompts em todos os
  transportes, com degradação honesta (método não suportado → lista
  vazia; porta morta → MCPError explícito, nunca silêncio).
- **RF-MCP-03** Tools nativas `mcp_recurso` (32ª) e `mcp_prompt`
  (33ª); seleção TF-IDF quando há muitos servidores.

### 5.11 Infra, CI/CD e portabilidade

- **RF-INF-01** CI nos 3 SOs (P0·T242): portões ruff → suíte →
  varredura; install editável; release.yml para tag.
- **RF-INF-02** `pluto gates` espelha o CI localmente; `pluto
  revisar` é gate único pré-push (varredura objetiva + revisor local
  com veredito JSON validado).
- **RF-INF-03** Portabilidade (`docs/PORTABILIDADE.md`): matriz de
  dívida declarada — `_NAO_PORTADOS` por SO, visível na suíte
  (⏭ pulados listados). **Dívida atual: 38 (windows) · 5 (macos) —
  alvo do P0.1.**
- **RF-INF-04** Autostart reversível (systemd user · LaunchAgent ·
  .bat), update em 1 comando, doctor, backups, heartbeat.
- **RF-INF-05** Grafo de código (v4.4.0): AST puro → SQLite; "onde
  está a lógica de X?" a custo zero de tokens.

---

### 5.12 Módulos operacionais (RFs resumidas — auditoria §3)

| Módulo | Responsabilidade (RF) |
|--------|----------------------|
| `specialists.py` | ADR-001: especialistas-como-ferramentas — veredito JSON com evidência VALIDADA em disco, pool grátis com fallback, DLP, exames de competência |
| `autonomy.py` | 3 níveis (cauteloso/padrao/autonomo) + hard gates inejociáveis + varredura pré-entrega do AUTÔNOMO |
| `mission.py` | Modo missão: 1 objetivo → subtasks encadeadas (reusa run_pipeline — herda estágios 4/6/7) |
| `dossie.py` | Dossiê de task por artefatos (evidências de eventos, revisão) |
| `mencoes.py` | @menções com D2 (v7.2.1: texto indentado não é código) |
| `procs.py` | Processos em background (start/logs/stop) |
| `recipes.py` | Receitas prontas de uma linha |
| `code_manager.py` | Gerente de código Claude — opt-in consciente (D5) |
| `activity.py` | Log de atividades (o quê/quando) |
| `extrair.py` | Extrator ÚNICO de JSON de resposta de modelo (DRY) |
| `agendacfg.py` | Contas Google Calendar + eventos estruturados |
| `skills_audit.py` | Auditoria do catálogo (injeção, estrutura, duplicatas, `## Exemplo` informativo) |

Funcionalidades COM RF indireta (fluxo/canais): n8n local (§5.8 GUI) ·
vault Obsidian (§5.3 camada 7) · cache de certeza (§5.6 método) · modo
prazo e /comandos (orchestrator §4).

## 6. Modelo de dados (`<data_dir>/`)

```
config.yaml                     chaves CONGELADAS (contratos.py, v6.4.0)
workspace/                      sandbox de arquivos padrão
conversations/sessions/*.json   conversas GLOBAIS + current.json
projetos/<slug>/…               NODES de projeto (P8 — ver 5.4)
tasks/state/S%04d.json          checkpoints (P1) · tasks/done/ · spool
diario.jsonl                    diário de trabalho (P1)
verificacoes.jsonl              auditoria da 2ª passada (P2)
autoavaliacoes.jsonl            auditoria da autoavaliação (P3)
skills/ (+ staging)             catálogo + rascunhos em aprovação
logs/agent.log                  log do agente (truncamentos registrados)
audit/ · backups/ · heartbeat.json
grafo.db                        grafo AST (v4.4.0)
models/                         whisper.cpp (multimodal local)
secrets (chmod 600)             tokens/chaves — NUNCA no repo
varredura-nomes.txt             nomes pessoais (privado, DLP)
HERMES.md                       instruções globais do operador
secretario.json                 estado do secretário (briefing/lembretes)
lembretes.json                  chaves de lembretes já avisados
notifications.json              central de notificações da GUI
orchestrator_tasks.jsonl        registro das tasks do orquestrador
pending_approvals.json          aprovações pendentes (gates de segurança)
session_goals.json              objetivos por sessão
schedules/                      agendamentos do scheduler
dossies/                        dossiês de task (evidências)
```

Tudo **local-first**: nada sai da máquina sem passar por D2/DLP.

---

## 7. Requisitos não-funcionais

- **NFR-01 Privacidade**: D2/DLP em TODO caminho externo; memória e
  dados pessoais nunca saem; varredura pré-push (CRÍTICO bloqueia;
  hook `pluto gates --instalar-hook`). **P8.2 (T257)**: segredos
  bloqueados no data-dir ATIVO (não só no `~/.pluto` fixo) e
  `~/.ssh`/`~/.aws`/`~/.gnupg` nunca são escopo de projeto.
- **NFR-02 Performance**: >50 s inaceitável; cache de planos, cache de
  prompt (prefixo estável), keep_alive, fluxo leve 3 níveis (v6.6.0).
- **NFR-03 Robustez**: escrita atômica em tudo que persiste —
  **helper único `pluto/atomic.py`** (P8.2·T259: tmp único por
  escrita, seguro sob concorrência) migrado em config.yaml,
  current.json, notifications.json, secretario.json, lembretes.json;
  falha de escrita é LOGADA (nunca silêncio) e o secretário mantém
  espelho em memória (sem loop de 15 s); crash no meio não corrompe;
  degradação honesta em toda dependência opcional; nunca-mudo.
- **NFR-04 Portabilidade**: 3 SOs × x86-64/ARM64; Unix-ismos só em
  `plataforma.py`.
- **NFR-05 Determinismo**: mesma entrada → mesma saída (ordenações
  estáveis; desempate por ts µs; nunca relógio como fonte de ordem).
- **NFR-06 Observabilidade**: marcadadores no log do CI (jaula REAL ×
  degradação; orçamento do prompt N/6000) — "verde" sempre acompanhado
  da PROVA do caminho que rodou.

---

## 8. Roadmap V9.0.0 e status honesto

Ordem aprovada pelo operador: **P0 → P7 → P3 → P1 → P2 → P4 → P5 → P6**
(+ P8 adicionado pela proposta de nodes). "Uma fase por vez: código +
testes + CI verde nos 3 SOs + docs + relatório."

| Fase | Entrega | Teste | Status |
|------|---------|-------|--------|
| P0 | CI/CD de verdade (3 SOs, portões) | T242 | ✅ 07/11 |
| P7 | Cérebro escalável (portões de capacidade) | T249 | ✅ 07/11 |
| P3 | Autoavaliação contra o pedido | T246 | ✅ 07/11 |
| P1 | Contexto durável (checkpoint + diário) | T243–T244 | ✅ 08/11 |
| P2 | 2ª passada anti-alucinação | T245 | ✅ 08/11 |
| P4 | Secretário proativo | T247–T248 | ✅ 08/11 |
| P5 | Skills do pedido (5 PT-BR) | T250 | ✅ 09/11 |
| P6 | Sandbox provado de verdade (git enjaulado, net=False) | T251 | ✅ 09/11 |
| — | Diretriz 7 no cerne (honestidade radical) | T252 | ✅ 09/11 |
| P8 | Projetos como nodes (grupo de conversas) | T253 | ✅ 09/11 · CI 42578961078 verde 3 SOs · 253/253 |
| P8.1 | Correção dos 3 bloqueadores da auditoria SDD (estágios 4/6/7 impostos no pipeline · git_run endurecido · DLP no secretário) | T254–T256 | ✅ 10/11 |
| P8.2 | Segurança/robustez da auditoria: M4 (segredos por data-dir + escopo sensível) · M7 (`✖` = falha) · M6 (helper atômico único + secretário sem loop) · M5 (hook pré-push) | T257–T260 | ✅ 10/11 |
| P8.3 | Alinhamento spec/docs: M8 (skills) · M9 (portões reservados + heurística por fronteira + escalada morta removida) · M11 (versão 9.0.0-dev, CHANGELOG/README, waitress, matriz py) · M12 (diretrizes/roadmap/mapa no repo) · §3/§6 (RFs dos módulos + modelo de dados) | T261 | ✅ 10/11 |
| P0.1 | Queimar dívida win/mac (43 testes) + T107 | — | ⏳ pendente |
| — | **Release v9.0.0** (suíte+ruff+varredura+checklist) | — | ⏳ após P0.1 |

**Definition of Done do secretário (aceitação V9)** — 7 itens em
`ROADMAP-V9-SECRETARIO.md` §4; destes, o **#6 (E2E REAL: 1 dia de uso
com Ollama local de pé)** e o #7 parcial (prova viva na máquina do
operador) **não são automatizáveis no CI — declarados pendentes**.

**Backlog declarado (não escondido)**: E2E cérebro real Ollama · QA
F1–F8 + Fase 2 · T107 (denylist × symlink) · 43 testes não portados
(P0.1) · nível `seccomp` do sandbox não provável no runner (fd) —
degrada para kernel.

---

## 9. Portões de release

1. Suíte 100% (253/253) local + CI verde nos 3 SOs (1ª tentativa é a
   meta; falha intermediária = lição no commit).
2. ruff `E9,F,B,PLE` limpo.
3. Varredura de segredos limpa (CRÍTICO = 0).
4. `CHECKLIST-PRE-RELEASE.md` conferido.
5. README + CHANGELOG + **esta SPEC** atualizados no mesmo ciclo.
6. Tag `vX.Y.Z` com mensagem de marco.

---

## 10. Cronologia (resumo — detalhe no CHANGELOG.md)

- **v1–v2 (2026)**: núcleo do chat, execução ao vivo, memória
  persistente, ferramentas manuais, Claude Code, web (DuckDuckGo),
  voz (Whisper local).
- **v3**: pipeline orquestrador/executor/revisor, GUI responsiva/PWA,
  MCP de e-mail, memória gerenciável, skills curadas, autonomia barata
  (cache de planos), provedores grátis c/ privacidade dura, modo
  missão, catálogo orçado.
- **v4.0.0 (ADR-001)**: modelo completo de agentes — especialistas,
  sandbox de kernel, varredura/DLP, contexto de projeto, loop de
  aprendizado, D1–D5. Depois: betterme, gateway Telegram/WhatsApp,
  arena, grafo, revisar, multimodal local.
- **v5**: modo vida (missões determinísticas) · fluxos n8n locais.
- **v6**: multiplataforma 3 SOs (PR#12), performance/bootstrap,
  roteador de cérebro, contratos/SSOT (v6.4.0), dispositivo universal,
  certeza determinística + concisão (ponytail), CBTA.
- **v7**: finanças (controle de gastos), Open Finance/Belvo, plano
  verificado (elephant-goldfish), baterias de uso real (achados de
  campo → defesas), vault Obsidian.
- **v8**: paridade de agente (edit_file, processos, perguntas),
  notebook (clone do NotebookLM) + OCR nativos, rename **Pluto**
  (v8.3.0), gestor de finanças completo, contas vinculadas, MCP
  paridade Genkit (SSE + recursos + prompts) — **v8.6.0 liberada**.
- **v9.0.0 (dev)**: o "secretário" — CI/CD real, portões de
  capacidade, autoavaliação, contexto durável, 2ª passada, secretário
  proativo, skills do pedido, sandbox provado, honestidade radical no
  cerne, **projetos como nodes**. Commits-chave: `96fa483` (P0) ·
  `630f407` (P7) · `f785d79` (P3) · `15fe255` (P1) · `22a71bc` (P2) ·
  `a23126f` (P4) · `0dd94f3` (P5) · `6619cab` (P6, jaula provada) ·
  `2804c81`+`89f8dbd` (Diretriz 7) · `e76f5ea` (P8).

---

## 11. Manutenção desta spec (regra SDD)

1. Comportamento muda → spec muda **no mesmo commit**.
2. Toda seção carrega status de verificação (teste/CI) — sem prova, é
   "não verificado".
3. Novas fases entram na tabela do §8 com teste e data.
4. Esta spec NÃO substitui: `POLITICAS.md` (lei), `docs/DIRETRIZES.md`
   (modo de trabalho), `docs/ROADMAP-V9-SECRETARIO.md` (plano),
   `docs/MAPA-FLUXOS-V9.md` (fluxos), `docs/PORTABILIDADE.md` (dívida),
   `CHANGELOG.md` (histórico) — ela os **referencia como fontes**
   (todos versionados no repo desde a P8.3 — auditoria M12).

*SPEC.md · Pluto Agente · v9.0.0-dev · 09/11/2026 · mantida junto com
o código que especifica.*
