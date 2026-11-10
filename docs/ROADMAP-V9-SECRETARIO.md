# 🗺 ROADMAP V9.0.0 — PLUTO, O SECRETÁRIO

> Aprovado em 07/11/2026 · base: auditoria completa do projeto em v8.6.0
> (241 testes verdes, working tree limpo, tag pushed)

**Missão:** o Pluto deixa de ser uma ferramenta que responde e vira o
**secretário e executor fiel** do operador — devolvendo tempo para
estudos e outras atividades. Requisitos do operador (literais):

1. Controles de **pipelines CI/CD para código**;
2. **Autonomia própria sem perder contexto** e sem alucinações demais;
3. **Autoavaliação**: verificar se está dentro do que foi pedido e se
   o que entrega está correto — antes de entregar.

### ⚡ Princípio 0 (diretiva do operador, 07/11/2026)

> **O MODELO É A BASE, NÃO O LIMITADOR.**

O agente é desenhado como ARQUITETURA independente de modelo: o
cérebro (local ou remoto, hoje ou amanhã) define apenas o NÍVEL de
execução. Trocar/upgradear o cérebro — novo modelo Ollama, provider
remoto mais forte, acesso pago que o operador ganhe — deve DEIXAR O
AGENTE MAIS CAPAZ sem refatorar nada. Nenhuma capacidade é
"só quando o cérebro melhorar" (exclusão): toda ela nasce atrás de um
**PORTÃO DE CAPACIDADE** (`capacidades(cfg)` — ver P7), pronta para
ligar. O hermes3:8b é o PISO de hoje, não o teto do projeto.

---

## 1. AUDITORIA COMPLETA (estado real, nov/2026)

### 1.1 Números

| Métrica | Valor |
|---|---|
| Testes | **241** (suíte 100% verde pré e pós-tag v8.6.0) |
| Tools nativas | 33 |
| Skills | 50 (PT-BR, formato SKILL.md) |
| Módulos / LOC | 69 / 20.235 |
| Páginas na GUI | 4 (Painel, Fluxos, Finanças, Contas) |
| Transportes MCP | 3 (stdio, Streamable HTTP, SSE clássico) |
| Vinculações externas | 9 (página Contas) |
| Dependências | 5 (flask, requests, PyYAML, rich, waitress) |
| Commits / tags | 130 / 103 |
| Processo | gates manuais: suíte ~8 min + ruff E9,F,B,PLE + varredura + CHECKLIST-PRE-RELEASE |

### 1.2 Por requisito do secretário — o que EXISTE × o que FALTA

**CI/CD — nota 3/10 (o maior gap do projeto).**
- Existe: gates manuais disciplinados (103 tags sem quebra), varredura
  anti-segredo pré-push, checklist de release, QA-do-QA na suíte.
- Falta: **ZERO pipelines automatizados** (`.github/workflows` não
  existe). A qualidade depende de alguém rodar os gates na mão. Sem
  CI multi-SO, a promessa Windows/macOS nunca rodou de verdade.

**Autonomia sem perder contexto — nota 6/10.**
- Existe: compactação de mensagens sem perder contexto (55% do ctx),
  memória persistente (fatos), vault Obsidian por escopos, goals
  retomados pós-restart, tarefas do daemon retomadas (v3.11), cache
  de certeza (pergunta repetida = 0 chamadas), níveis de autonomia
  com hard gates + `perguntar_operador`, supervisor MCP com
  auto-restart e backoff.
- Falta: **checkpoint estruturado por tarefa** (o que já fiz / o que
  falta / onde travei — hoje uma tarefa longa que cai reinicia do
  zero ou depende do histórico do chat); alerta quando o contexto é
  truncado (perda silenciosa); "diário de trabalho" consultável.

**Anti-alucinação — nota 7/10.**
- Existe: respostas grounded no notebook (verbatim + [n], "não está
  nas fontes" é resposta válida), camada de certeza (só entra Q&A
  validado), revisão por 2º modelo + arena, ferramentas que retornam
  dados reais (a ferramenta calcula, o modelo nunca soma),
  `extrair.py` com chaves balanceadas, guards anti-recusa e
  anti-erro, D2/DLP.
- Falta: **verificação de saída contra os dados das tools em tarefas
  gerais** (só o notebook tem grounding); medida de confiança
  visível; protocolo de "incerto → confirmar antes de agir" para
  ações destrutivas.

**Autoavaliação — nota 2/10 (quase inexistente em runtime).**
- Existe: QA-do-QA (a suíte se avalia), guards no agent, honestidade
  de degradação em toda a cadeia.
- Falta: **o agente NÃO confere a própria entrega contra o pedido**.
  Nada deriva critérios de aceitação do pedido do operador nem
  apresenta quadro ✅/⚠️/✖ no fim. É o requisito mais explícito e o
  menos atendido.

**Funções de secretário — nota 7/10.**
- Existe: agenda Google (ler + criar), e-mail (ler/enviar opt-in),
  Telegram/WhatsApp, gestor financeiro completo, tarefas agendadas +
  daemon, notebook de estudos com materiais, MCP aberto ao ecossistema.
- Falta: **proatividade** — o Pluto nunca toma a iniciativa: sem
  briefing matinal, sem lembrete de evento chegando, sem triagem de
  e-mail. Secretário que espera ser chamado é metade de um secretário.

### 1.3 Riscos estruturais (mantidos na radar)
- Cérebro local hermes3:8b é o elo fraco (guards existem por isso);
  num_ctx 8192 limita tarefas longas.
- Bus factor 1; suíte monolítica (10k linhas, 1 arquivo, ~8 min).
- Contratos implícitos: `Agent.run` devolve erro como string (já
  mapeado; tratado no notebook, não no resto).

---

## 2. VALIDAÇÃO DAS FONTES EXTERNAS (o que vale, com o modelo atual)

| Fonte | O que é | Veredito | Por quê |
|---|---|---|---|
| **ykdojo/claude-code-tips** | 45+ dicas de uso do Claude Code + plugin dx; 742 commits, ativo | ⭐ NÃO instalar — **absorver 3 ideias** | É conteúdo sobre USAR o Claude Code, não skills de runtime. As 3 ideias que valem: (1) TESTING.md como *log de revisão contínuo* → nosso padrão "achado de campo vira regressão" ganha um arquivo de log; (2) "Claude rodando em container" → confirma o sandbox do nosso roadmap; (3) regression-baseline antes de mudança → reforça o gate de suíte pré-commit |
| **nidhinjs/prompt-master** | Skill que escreve prompts precisos: 9 dimensões de intenção, **máx. 3 perguntas esclarecedoras**, auditoria de tokens | ✅ **ADAPTAR 1 skill PT-BR** | O pipeline dele é exatamente o que um secretário precisa ANTES de executar: extrair intenção, critérios de sucesso e perguntar pouco e bem. Encaixa no nosso `perguntar_operador`. A skill cru (inglês, longa) não renderia no 8b — adaptada e curta, sim |
| **`npx convez-ai …`** | — | ⚠️ **não existe** | Não achei o pacote "convez-ai" no npm. O comando real do ecossistema é `npx skills add <owner/repo>` (CLI "skills" da Vercel Labs). De qualquer forma, **não precisamos**: o Pluto já tem `pluto skills import owner/repo` nativo (baixa tarball, acha SKILL.md, instala) |
| **alirezarezvani/claude-skills** | 192–410 skills (marketing, produto, engenharia, compliance, C-level…) + 7 personas | 🚪 **CATÁLOGO POR PERFIL (P7)** | O catálogo entra no system prompt — perfil LEVE (8b local, ctx 8k) carrega só as essenciais PT-BR; perfil FORTE (cérebro grande, ctx amplo) carrega o catálogo expandido, incluindo absorção ampla deste repo. `pluto skills import` já instala; o FILTRO por capacidade é que passa a existir |
| **trycua/cua** | Infra de computer-use agents (31,8k★, MIT): sandboxes, SDKs, drivers de desktop, benchmarks | 🚪 **PORTÃO DE CAPACIDADE (P7)** | Operar desktop por screenshot+clique exige cérebro forte e sandbox — fica atrás do portão `computer_use`, integrado via MCP quando o perfil de cérebro suportar (o Pluto já fala MCP; nada a refatorar depois). bwrap continua sendo o caminho leve para shell |
| **mattpocock/skills** | ~24 skills MIT de engenharia (write-a-prd, prd-to-plan, prd-to-issues, grill-me, TDD, review de diff) — top trending | ✅ **ADAPTAR 4 (as de pedido/planejamento)** | `write-a-prd` + `prd-to-plan` + `grill-me` formam EXATAMENTE o fluxo "entendi o pedido → entrevistei → planejei em fases" que o executor fiel precisa; casam com nossos `fluxos` e `tasks`. `grill-me` (interrogar até resolver o design) é o `perguntar_operador` turbinado. Adaptar: PT-BR, curtas, com exemplo — não importar cru |

**Resumo da validação:** das 6 fontes, **2 valem a pena** (prompt-master
e mattpocock — ambas ADAPTADAS, não importadas), 1 não existe
(convez-ai), 1 é referência de ideias (ykdojo), 2 não se aplicam ao
modelo/escopo atual (cua, claude-skills em massa). O mecanismo de
instalação (npm de skills) já temos nativo — e é melhor: `pluto skills
import` não exige Node.

**Regra de ouro (recalibrada pelo Princípio 0):** skill externa não é
recusada por causa do modelo — é GRADUADA. No perfil leve entra
traduzida/encurtada/com exemplo (senão o 8b ignora ou alucina); no
perfil forte entra completa. A skill vive no catálogo com um campo de
nível mínimo; o carregador filtra pelo cérebro ATIVO da sessão.

---

## 3. ROADMAP V9.0.0 — FASES

### P0 — CI/CD de verdade (o gap #1) · T242 — ✅ ENTREGUE (07/11/2026)
- **GitHub Actions**: em cada push/PR → ruff `E9,F,B,PLE` + suíte
  completa + varredura na **matriz ubuntu|windows|macos** (a promessa
  multi-SO finally verificada por máquina). Na tag `v*` → release
  automática: refaz os 3 portões, `git archive` zip (só rastreados) e
  GitHub Release com o asset — sem passo manual.
- **`pluto gates`** local: 1 comando = ruff + suíte + varredura,
  espelho exato do CI (para no primeiro portão que falha; `--lista`).
- **Prova ao vivo** (3 pushes, 3 rodadas): run 42340204729 pegou 43
  testes POSIX-only (38 win + 5 mac) que 103 tags manuais nunca viram
  → dívida RASTREADA (P0.1 abaixo); run 42342047644 pegou bug REAL de
  determinismo no arena (mock media tempo por relógio — corrigido no
  P0.2, commit 3939eeb); run **42343666440: SUCCESS nos 3 SOs** —
  ubuntu 242/242 · windows 204+38 pulados contados · macos 237+5
  pulados contados · varredura limpa nos 3.
- Commits: 96fa483 (workflows+gates+T242) · 05c883f (P0.1 dívida
  rastreada) · 3939eeb (P0.2 arena determinístico).

### P8 — Projetos como NODES (proposta do operador) · T253 — ✅ ENTREGUE (09/11/2026)
- Proposta: "Projeto → RPG: Conversas, Contextos etc, Recursos/artefatos
  gerados" — semântica confirmada: **o node é, por dentro, um GRUPO DE
  CONVERSAS**.
- `<data>/projetos/<slug>/`: conversas (store escopado, ponteiro próprio),
  contexto (contexto.md + anotações datadas), artefatos gerados; tool 37ª
  `projeto` + CLI `pluto projeto` + `/api/chat` com "projeto" (inexistente
  → 400 explícito); isolamento global×node provado (T253, 11 blocos).
- Commits: e76f5ea · SPEC.md (especificação-mestre SDD) criada.

### P8.1 — Correção dos 3 BLOQUEADORES da auditoria SDD · T254–T256 — ✅ ENTREGUE (10/11/2026)
- Auditoria externa de conformidade validada claim por claim
  (docs/VALIDACAO-AUDITORIA-SDD.md, com PoCs reproduzidos).
- **A1 → T254**: estágios [4] checkpoint, [6] verificação e [7]
  autoavaliação IMPOSTOS pelo run_pipeline (mission herda) — entrega de
  task sai com rodapé ✓/✗/~ + confiança e quadro; conversa segue leve.
- **A2 → T255**: git_run com denylist na tool (config que executa
  comandos: fsmonitor/sshCommand/hooksPath/pager/editor/alias ·
  `--output` bloqueado) — os 2 PoCs da auditoria viraram regressão.
- **A3 → T256**: secretário com DLP no envio (mascarar + e-mail
  corporativo — lacuna que o T256 expôs: DLP global só cobria domínios
  pessoais).

### P8.2 — Segurança e robustez da auditoria SDD (M4·M5·M6·M7) · T257–T260 — ✅ ENTREGUE (10/11/2026)
- **M4 → T257**: segredos bloqueados no data-dir ATIVO (o fixo
  ~/.pluto não cobria --data-dir customizado — PoC da auditoria) e
  ~/.ssh/~/.aws/~/.gnupg nunca são escopo de projeto.
- **M7 → T258**: `✖` também é falha no execute_tool (≥7 tools
  retornavam erro honesto com ok=True).
- **M6 → T259**: helper ÚNICO `pluto/atomic.py` migrado nos 5 pontos
  citados; falha de escrita LOGADA + espelho em memória no secretário
  (fim do risco de briefing em loop de 15 s). No caminho, o T71 pegou
  uma race de tmp compartilhado que a própria migração introduziu —
  tmp agora é único por escrita (pid·thread·seq), com regressão de
  concorrência no T259.
- **M5 → T260**: `pluto gates --instalar-hook` grava o hook pré-push
  (varredura bloqueia o push ANTES de sair; hook alheio preservado).

### P0.1 — Queimar a dívida de portabilidade (39 únicos) · EM CURSO (lote 2/≈5)
- **Lote 1 ✔ (10/11)**: T107-mac — bug REAL de segurança corrigido
  (deny nos dois planos: /etc→/private/etc não escapa) + prova de
  symlink na suíte. Restam 38 (37 win · 4 mac).
- **Lote 2 ✔ (10/11)**: grupo A win (5) — T164/T165/T170/T171/T227
  portados com fakes `.cmd` gerados por SO; a porta expôs **5 bugs
  reais de produto** corrigidos no mesmo commit: `procs.start`
  (`start_new_session` fixo → ValueError no win), `procs.stop`
  (`killpg` inexistente → AttributeError), `plataforma.matar` sem
  `/T` (órfãos), `fluxos.n8n_bin` sem o shim `n8n.cmd` do npm,
  `multimodal` decodando cp1252 (whisper.cpp emite UTF-8). Restam
  33 (32 win · 4 mac).
- Lotes seguintes: B-caminhos (≈10) · C-prompts POSIX (3) ·
  D-produto (T98/T174/T188) · E-guards (2) · F-update (3) ·
  G-triagem (11).

### P0.1 — Queimar a dívida de portabilidade (43 testes) · NOVO
- `docs/PORTABILIDADE.md` lista cada teste com causa e prioridade;
  portar = corrigir + remover de `_NAO_PORTADOS` + CI revalida nos
  3 SOs. Guarda no runner: nome fantasma na lista falha o pipeline.
- **Prioridade**: T107 (deny-list não resolve `/etc`→`/private/etc`
  no macOS — bug de SEGURANÇA do produto) → T174/T98 (autostart e
  diagnóstico multi-SO) → grupo WinError 193 (5 de uma vez) → resto.
- Encaixa junto das fases (ex.: T174 na P6/sandbox, T98 na P4).

### P1 — Contexto durável (autonomia sem perder contexto) · T243–T244 — ✅ ENTREGUE (08/11/2026)
- **Feito**: `pluto/contexto.py` — checkpoint por tarefa em
  `tasks/state/<id>.json` (escrita atômica, merge sem perder feitos,
  critérios extraídos do objetivo, ids S000x), `retomar()` reconstrói
  a tarefa a frio ("continua a tarefa X"), truncamento REGISTRADO no
  agent.log (fim da perda silenciosa), diário `diario.jsonl`
  consultável por dia + espelho no vault Obsidian (escopo `diario`),
  tool `tarefa_checkpoint` (35ª). **Bug real pego pelo CI** (run
  42503471387): empate de 1 s no "mais recente" caía na ordem do
  filesystem → fix com ts em µs + regressão 6b. Commits 15fe255 +
  2f2d36c · CI run 42505514444 SUCCESS nos 3 SOs · 246/246.
- **Checkpoint por tarefa**: `<data>/tasks/state/<id>.json`
  (objetivo, critérios, feitos, próximos, bloqueios, última tool) —
  atualizado a cada passo do Agent; retomada a frio ("continua a
  tarefa X" reconstrói o estado sem reler o chat todo).
- **Alerta de truncamento**: quando a compactação corta, o agente SABE
  e informa (fim da perda silenciosa de contexto).
- **Diário de trabalho**: 1 linha por tarefa concluída no vault
  (o que/quando/fonte) — memória consultável de médio prazo.

### P2 — Anti-alucinação com verificação de 2ª passada · T245 — ✅ ENTREGUE (08/11/2026)
- **Feito**: `pluto/verificacao.py` — extração determinística de
  afirmações factuais (números/verbos/absolutos; opinião declarada não
  é fato), checagem contra os dados reais das ferramentas (✓ lastreada
  · ✗ sem lastro → corrigir · ~ incerta → DECLARAR), score de
  confiança no rodapé, regra dura: destrutiva com ✗ ou <80% →
  `perguntar_operador` (tool que já existia); cérebro julga com o
  portão `verificacao_completa` (P7); auditoria `verificacoes.jsonl`
  sem vazar a resposta (D2); tool `verificar_resposta` (36ª) com a
  instrução na DESCRIPTION (canal real de descoberta — o SYSTEM_PROMPT
  tem orçamento T12 <6000 já consumido pelo ambiente). **2 aulas de
  CI**: T12 anti-inflação pegou o prompt (P2.1) e meu assert numérico
  em componente variável por SO era flake (P2.3). Commits 3ad49ce →
  22a71bc · CI run 42526209477 SUCCESS nos 3 SOs · 247/247 (T245).
- Após gerar resposta em tarefa com tools, uma **passada barata de
  verificação**: cada afirmação factual é conferida contra os dados
  que as tools retornaram → marca ✓ (com fonte interna) / ✗ (corrige)
  / ~ (incerto — DIZ que é incerto).
- **Score de confiança** no rodapé da resposta; confiança baixa +
  ação destrutiva → `perguntar_operador` obrigatório.

### P3 — AUTOAVALIAÇÃO (o pedido explícito) · T246 — ✅ ENTREGUE (07/11/2026)
- **Feito**: `pluto/autoavaliacao.py` — critérios extraídos DO PRÓPRIO
  PEDIDO (heurística PT-BR determinística), cada um julgado contra a
  entrega e as saídas reais das ferramentas (✅ com evidência · ✖ com
  causa · ⚠️ declarado), veredicto entregar/corrigir/revisar + score,
  auditoria em `autoavaliacoes.jsonl` (+resumo no log sem vazar o
  pedido, D2). Cérebro julga quando `verificacao_completa` abre (P7),
  com fallback honesto. Tool nativa `autoavaliar` (34ª, com
  `dados_tools`). Commit f785d79 · CI run 42500300843 SUCCESS nos
  3 SOs · 244/244 (T246).
- **Checklist de aceitação derivado do pedido**: no início da tarefa,
  o agente extrai os critérios do que foi pedido (com as skills
  adaptadas do prompt-master/mattpocock); no fim, confere item a item
  e entrega quadro final:
  `✅ feito · ⚠️ parcial (por quê) · ✖ não feito (por quê)`.
- Registro no audit (a autoavaliação vira dado auditável, não só
  frase bonita). Mentir no quadro = falha de teste E2E.

### P4 — Secretário proativo (o tempo de volta pro operador) · T247–T248 — ✅ ENTREGUE (08/11/2026)
- **Feito**: `pluto/secretario.py` — briefing diário no Telegram
  (agenda + e-mails triados + tarefas ativas + diário de ontem; 1×/dia,
  falha retenta 1×/h e sucesso zera o backoff), lembretes de agenda
  (`lembrete_min`, 1×/dia por evento, sem spam;
  `agendacfg.eventos_estruturados` novo), triagem de e-mail IMAP
  ("precisa de você" × informativo, resumo no briefing), `tick()` no
  Scheduler (mesmo padrão do autoscan, nunca derruba o loop), CLI
  `pluto secretario status|briefing [--enviar]`. Tudo opt-in
  (`briefing_on`, `briefing_hora`, `lembrete_min`,
  `email_triagem_on`) e injetável. Commit a23126f · CI run
  42532955438 SUCCESS nos 3 SOs (1ª tentativa) · 249/249 (T247–T248).
- **Briefing diário** (daemon, horário configurável): agenda do dia +
  faturas a vencer + resumo de finanças + e-mails não lidos importantes
  + tarefas do dia → entregue no Telegram/WhatsApp.
- **Lembretes de evento**: 30 min antes (configurável), via gateway.
- **Triagem de e-mail**: não lidos → prioridade + 1 linha de resumo
  (cabeça local; nada de conteúdo sensível em provedor externo).

### P5 — Absorção das skills validadas — ✅ ENTREGUE (09/11/2026)
- **Feito**: 5 skills PT-BR curtas com exemplo e gatilhos nossos,
  GRADUADAS por `nivel` (P7): `pedido-fiel` (prompt-master: eco
  literal + 9 dimensões + máx 3 perguntas + suposição declarada),
  `escrever-pedido` (PRD curto DEVE/MELHOR TER/NÃO FAZER),
  `pedido-para-plano` (passos com ação+ferramenta+pronto →
  checkpoint), `interrogar` (grill-me, nivel rapido — some do
  cérebro leve), `autoavaliar-entrega` (ritual P2+P3: verificar →
  autoavaliar → checkpoint → rodapé). **T250** valida tudo +
  catálogo inteiro (55 skills) limpo na auditoria. Commit 0dd94f3 ·
  CI run 42542209050 SUCCESS nos 3 SOs · **250/250 — alvo do
  roadmap batido**.

### P6 — Sandbox de execução (quando o host permitir) — ✅ ENTREGUE (09/11/2026, escopo corrigido pela auditoria)
- **Descoberta**: o roadmap subestimou a v4.0.0 — `sandbox_kernel.py`
  (bwrap ro-bind + workspace rw + seccomp BPF à mão + degradação
  honesta) JÁ existia e o `run_command` já rodava enjaulado.
- **Feito de verdade**: tool `git_run` também na jaula e, como
  `_GIT_OK` é só operação local, com **rede desligada no kernel**
  (net=False); CI instala bubblewrap no Linux e o **T251 prova a
  jaula REAL a cada push** (escrever fora falha · dentro funciona ·
  net=False não conecta · BPF estruturado · wiring do git) — com
  marcador visível no log; Ubuntu 24.04 bloqueia userns não
  privilegiado (AppArmor) → CI libera o sysctl no runner (lição do
  run 42555505782). Fundação do portão `computer_use` pronta.
  T107 (denylist não resolve symlink) segue como prioridade 1 do P0.1.
  Commit 301b5a2 · 251/251.

### P7 — CÉREBRO ESCALÁVEL (o Princípio 0 virando mecanismo) · T249 — ✅ ENTREGUE (07/11/2026)
- **Feito**: `pluto/capacidades.py` (perfil leve|rapido|forte + 5 portões,
  `cerebro_ativo` espelhando a decisão real do agente), override
  `capacidades_perfil` no config, skills graduadas por `nivel` no
  frontmatter (catálogo filtra; inventário não), `solicitar_escalada`
  (avali do operador, nunca silenciosa; entrega no Telegram na P4),
  CLI `pluto capacidades`. **T249** prova o DoD item 7: gemini-2.5-pro
  só trocando CONFIG → todos os portões abertos, sem mexer em código.
  Commit 630f407 · CI run 42346221810 SUCCESS nos 3 SOs · 243/243.
- **`capacidades(cfg)`** (novo módulo): lê o cérebro ATIVO (provedor +
  modelo + ctx do REGISTRY/config) e expõe o PERFIL e os PORTÕES —
  `verificacao_completa`, `skills_avancadas`, `ctx_longo`,
  `computer_use`, `autonomia_estendida`. Um lugar só, consultado pelo
  Agent/skills/verificação — nada no código pergunta "que modelo é?"
  de forma espalhada.
- **Perfis**: `leve` (local 8b) · `rapido` (Groq/Mistral…) · `forte`
  (modelos grandes). Trocar de provider no config muda o comportamento
  NO PRÓXIMO boot, sem refatorar.
- **Auto-escalonamento por tarefa** (com aval do operador, nunca
  silencioso): tarefa crítica/complexa com cérebro forte disponível →
  o supervisor pode solicitar a escalada (política em POLITICAS.md,
  gastando quota remota só quando valer).
- **Skills por perfil** (P5 já entrega as adaptadas; P7 adiciona o
  filtro por nível mínimo no carregador).
- **Portão computer-use**: integração cua via MCP documentada e
  desligada até `computer_use=True` — ligar não exige reescrita.

### Release v9.0.0 (major = novo papel)
- Bump 8.6.0 → 9.0.0, CHANGELOG/README/MAPA/gen_doc, gates, CI
  publicando a release sozinho, zip.
- **Testes-alvo: 241 → ~250** (T242–T249).

---

## 4. DEFINITION OF DONE DO SECRETÁRIO (aceitação da V9)

1. Push sem CI verde não entra mais (P0). ✔ verificável por máquina.
2. Tarefa longa cai e retoma do checkpoint, sem repetir passo (P1).
3. Resposta de tarefa com dados vem com verificações ✓/✗/~ e confiança
   visível; incerto + destrutivo pergunta antes (P2).
4. Toda entrega termina com o quadro de autoavaliação contra o pedido
   original — e o quador bate com a realidade (P3).
5. O operador acorda com o briefing no Telegram sem pedir nada (P4).
6. E2E REAL na máquina do operador: 1 dia de uso do secretário com
   Ollama local de pé — jornada completa, não só testes.
7. **PROVA DO PRINCÍPIO 0**: trocar o cérebro no config (ex.: apontar
   para um provider forte) e reiniciar → verificação mais profunda,
   mais skills ativadas, autonomia estendida — SEM mexer em código
   (testado por T249 com dois perfis).

## 5. CUSTO POR NÍVEL DE CÉREBRO (calibração, NÃO limite)
- Verificação de 2ª passada e autoavaliação são ARQUITETURA (sempre
  presentes); o que o perfil muda é a PROFUNDIDADE: leve = passada
  única com checklist; rápido = completa, imperceptível; forte =
  completa + re-checagem cruzada.
- Perfil leve (8b local): +15–40 s por resposta complexa — aceitável
  para secretário em segundo plano; o auto-escalonamento do P7 resolve
  o caso urgente.
- Skills externas: graduadas por nível mínimo (seção 2) — nunca
  recusadas, sempre graduadas.
- Computer-use: atrás do portão `computer_use` (P7) — liga no dia em
  que o cérebro ativo suportar, sem refatoração.

## 6. REGRAS QUE NÃO MUDAM
Local-first · D2 (código/segredos nunca saem) · dados pessoais fora do
repo · PT-BR · suíte 100% + ruff + varredura antes de tag · achado de
campo vira regressão · honestidade antes de promessa · testar antes de
criar · validar de verdade.

---
*ROADMAP-V9-SECRETARIO.md · aprovado 07/11/2026 · Princípio 0 adicionado
por diretiva do operador: O MODELO É A BASE, NÃO O LIMITADOR. Ordem
recomendada: P0 → P7 → P3 → P1 → P2 → P4 → P5 → P6 (CI protege tudo;
capacidades logo cedo porque todos os portões dependem dele;
autoavaliação é o pedido mais explícito).*
