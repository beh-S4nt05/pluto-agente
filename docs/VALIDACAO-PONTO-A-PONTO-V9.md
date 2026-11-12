# 🔎 VALIDAÇÃO PONTO A PONTO — auditoria externa nº 2 · plano de cobertura 89%

> **Fonte:** análise externa que leu **12 documentos** do projeto (sem
> código-fonte e sem logs do CI), recebida em 11/11/2026.
> **Método da contraprova (este documento):** cada afirmação foi
> re-verificada contra o **repo vivo** — código (`arquivo:linha`),
> suíte (261 casos) e logs do CI de hoje (runs 42906963094,
> 42925967767, 43031210782, todos verdes nos 4 jobs). Nada foi aceito
> por leitura de documentação — a regra da casa é *prova honesta*.
>
> **Status:** ✔ confirmado (o problema é real) · ⚠ parcial/nuance ·
> ✖ desatualizado (o auditor leu versão velha; evidência do estado
> atual) · 🔎 continuar (passo definido abaixo).
>
> **Resumo:** 23 pontos verificados · **11 confirmados** ·
> **6 parciais** · **5 desatualizados** · 1 sem efeito prático.

---

## §0 — Por que boa parte veio desatualizada

O auditor leu um **mix de documentos de épocas diferentes** (docs da
raiz de v2–v3 junto com os atuais). Exemplos: citou "43 testes
pulados" (estado de 07/11) quando hoje são **16 no Windows e 0 no
macOS**; disse que o P0.1 "não está agendado antes do v9.0.0" quando
ele está **em curso** (lotes 1–4 fechados com CI verde); a matriz do
CI "só eixo de SO" quando a P8.3 adicionou **py 3.11 + 3.13**.

A **causa raiz apontada pelo auditor é correta e aceita**: números
digitados à mão em ~12 documentos + `tools/gen_doc.py` misturando
prosa estática velha com tabelas geradas → a melhoria §4.10 (fonte
única + teste de divergência) entra no plano.

## §0.1 — Números AUTORITATIVOS de hoje (medidos, não digitados)

| Medida | Valor | Como foi medido |
|---|---|---|
| Rotas da API/GUI | **110** | `len(list(app.url_map.iter_rules()))` |
| Tools nativas | **37** | `len(TOOL_NAMES)` |
| Skills builtin | **55** | `ls -d skills/*/SKILL.md \| wc -l` |
| Testes | **261** (261/261 nos 4 jobs do CI) | suíte + logs do CI |
| **Cobertura de linha** | **68%** (14.273 stmts · 4.615 miss) | `coverage run --source=pluto tests/run_all.py` — relatório completo em `docs/COBERTURA-BASELINE-2026-11-11.txt` |
| Python declarado | `>=3.9` (pyproject) · CI cobre 3.11+3.13 | PORTABILIDADE §Python declara 3.9/3.10 como análise estática |

---

## §1 — Segurança e privacidade

### 1.1 ⚠→✔ Privacidade maior que a garantia (D2 não cobre dado pessoal de tool)
**Confirmado.** `payload_sensivel()` (llm_providers.py) decide D2
apenas via `mascarar()` — código/segredos/injeção. A **saída** de
e-mail, agenda, finanças, notebook e vault não é marcada como
sensível: se o cérebro ativo for um provedor gratuito, esse conteúdo
pode sair da máquina. Os termos citados (Gemini gratuito: uso para
treinamento, revisores humanos, "não envie dados pessoais") tornam o
risco real.
**Ação (aceita, §4.1):** sensibilidade **por ferramenta** — tool que
devolveu dado pessoal fixa o resto do loop no cérebro local (como o
D2 já faz para código) + texto do README corrigido.

### 1.2 ✔ Sem defesa documentada contra injeção de prompt indireta
**Confirmado.** Só skills passam por auditoria. Conteúdo de
`web_fetch`, e-mail, MCP e WhatsApp entra no contexto de um agente
com shell e agendador; o guard de execução executa o que o modelo
escreveu.
**Ação (aceita, §4.3):** saída de web/e-mail/MCP tratada como dado
não confiável; após ler esse conteúdo, egress (e-mail, rede, novo
agendamento) exige aprovação; guard de execução desliga o auto-exec
nesse estado (OWASP LLM01).

### 1.3 ✔ Servidor local: DNS rebinding e token fraco — **o ponto mais grave**
**Confirmado, com 3 evidências no código:**
- `guard_cross_origin_posts` (app.py:80) valida Origin **só em
  POSTs**; GETs não validam Origin e **ninguém valida `Host`** →
  DNS rebinding possível (a spec MCP exige Origin em toda conexão);
- `auth_token` default `""` (config.py:81) — token **opcional**;
- `@protected` aceita token via **query string**
  (`request.args.get("token")`, app.py:109) e o scheduler **recomenda
  `?token=...`** na URL do webhook (app.py:1555) → token em logs e
  histórico de navegador.

Nuance: `--host 0.0.0.0` hoje **nem avisa** (o auditor achou que
avisava); o default é loopback — mas bind em 0.0.0.0 sem token é
aceito silenciosamente.
**Ação (aceita, §4.2):** validar **Host e Origin** contra lista em
toda conexão; recusar bind fora de loopback sem token; segredo por
webhook **no header** com `hmac.compare_digest`; **teste que percorre
o `url_map`** (110 rotas) e falha se rota nova ficar sem auth — mata
também a dúvida "71/71 era da v3.14.2".

### 1.4 ✔ Segurança desigual entre SOs (+ 1 nuance que joga a favor)
**Confirmado:** jaula REAL (bwrap+seccomp) só Linux (PORTABILIDADE
declara); chmod 600 é inócuo no Windows (T41 tem branch própria;
ACL = backlog do release).
**Nuance:** o temor "BPF escrito à mão sem checar arquitetura" **não
se confirma** — `sandbox_kernel.py:47-49` carrega a arch e
**EPERM em arch estranha** (falha fechada, não aberta). O que existe,
documentado no próprio módulo: aarch64 **fica sem seccomp** (só
bwrap). T251 prova a jaula em Linux x64 — ARM segue como gap.

### 1.5 ✖ "T107 ainda aberto · 43 pulados · P0.1 depois do v9"
**Desatualizado.** T107 foi corrigido no **P0.1 lote 1** (deny nos
dois planos, `/etc`→`/private/etc` não escapa; prova de symlink na
suíte; CI verde com o teste rodando em Windows E macOS). Pulados
hoje: **16 win · 0 mac** (era 38·5). O P0.1 está **em curso, antes da
tag** — lotes 1–4 fechados, restam E+F (5) e G (11).

### 1.6 ✔ Update sem verificação de integridade
**Confirmado.** Há defesa zip-slip, mas **sem checksum/assinatura**
(update.py não tem sha256) e `garantir_entry_points` roda
`pip install -e . --no-deps` (update.py:147,164) → dependência nova
numa release não é instalada; arquivos removidos upstream ficam.
**Ação (aceita, §4.4):** publicar **SHA256SUMS** (ou attestation) e
verificar antes de aplicar; instalar dependências no fluxo.

---

## §2 — Qualidade e arquitetura

### 2.1 ✔ Suíte 100% mock · harness com modelo real no backlog · DoD#6 pendente
**Confirmado** (auto-declarado no CHECKLIST). **Ação (aceita, §4.5):**
job noturno com Ollama real + modelo pequeno, 5–8 cenários de ouro do
selftest, asserções tolerantes — nos runners públicos (gratuitos,
4 vCPU/16 GB).

### 2.2 ✔ "Confiança" 0–100 é heurística
**Confirmado.** Extração lexical; no perfil leve o mesmo 8B que gerou
avalia. **Ação (aceita, §4.8):** renomear para **"cobertura de
evidência"** (% de afirmações com lastro), calibrar com 30–50 casos
rotulados; no perfil leve, revisor ≠ gerador sempre que existir.

### 2.3 ⚠ Perfil de capacidade por nome do modelo
**Confirmado com nuance:** `capacidades.py` se autodeclara
"heurísticas de nomes (honestas, não mágicas)". Quebra com MoE e
quantização. **Ação (backlog):** mini-benchmark (selftest/arena) ao
trocar de provedor; nome vira fallback.

### 2.4 ⚠ Contexto no limite
**Parcial.** Tools são **37** (não 36) e o catálogo é **orçado por
nível** (skills avançadas não entram em cérebro leve); `num_ctx` é
configurável. A compactação é estimativa — e por **chars**, que
subestima em PT-BR (AC/tilde contam 1, tokens >1). **Ação (aceita,
§4.6):** usar `prompt_eval_count` do Ollama (tokens reais) para
compactação e alerta de truncamento.

### 2.5 ⚠ Waitress + SSE
**Parcialmente desatualizado:** hoje são **threads=16**
(app.py:2189), não 8. O risco de fundo persiste: cada stream (chat ao
vivo, log ao vivo) ocupa uma thread. **Ação (backlog):** medir com 5
abas; se travar, limitar streams ou trocar o log ao vivo por polling.

### 2.6 ⚠ Estimativas de tempo incoerentes
**Parcial.** GUIA "0,5–2,4 tok/s" e ROADMAP "+15–40 s" são estimativas
de épocas diferentes (hardware-dependentes); o ">100 s" do docs.md é
linha de **diagnóstico de problema** (tabela de sintomas), não
promessa. A incoerência real vem dos docs velhos na raiz.
**Ação (§4.10):** docs históricos para `docs/historico/` com aviso.

### 2.7 ⚠ MCP: transporte descontinuado + header de versão
**Confirmado no cliente.** `mcp_client.py` mantém SSE legado (o
external auditor acerta: descontinuado como transporte avulso desde
2024-11-05) e envia `protocolVersion` **no body do initialize**
(mcp_client.py:77), mas **não envia o header
`MCP-Protocol-Version`** exigido nas revisões 2025+ em todo POST.
**Ação (aceita, §4.7):** enviar o header; tratar SSE como legado.

### 2.8 ✖/✔ CI com cobertura estreita
**Desatualizado no eixo:** a matriz tem **SO × Python (3.11+3.13)**
desde a P8.3 (4 jobs verdes). **Válido no resto:** sem ARM64, sem
type-check, **sem cobertura medida** (até este documento), ruff só
`E9,F,B,PLE`, suíte monolítica de ~8 min, e `requires-python >=3.9`
convivendo com docs.md "3.10+" (3.9 saiu de suporte em out/2025).
**Ação (aceita, §4.9 + §5):** medir cobertura no CI **a partir deste
baseline**; subir o mínimo para 3.11 na v9 (quebra declarada);
ARM64 (`ubuntu-24.04-arm`, `windows-11-arm` — GA e grátis em repo
público); pip-audit + Dependabot; secret scanning do GitHub como
segunda camada.

### 2.9 ✖/⚠ Dependências
**Desatualizado:** `waitress>=3.0` **está** no `requirements.txt` e no
`pyproject.toml` (o auditor não recebeu os arquivos de build).
**Válido:** sem limites superiores e sem lockfile. **Ação (backlog):**
lockfile (pip-compile/uv) no release.

### 2.10 ✖/⚠ Licenças
**Desatualizado em parte:** `LICENSE` **existe** na raiz (o auditor
leu "o material enviado" — 12 docs, sem o LICENSE). **Válido:**
`NOTICE` não existe; skills adaptadas (mattpocock · spec-kit ·
prompt-master) precisam de **conferência de licença e atribuição** —
é a ação real daqui.

---

## §3 — Erros de documentação (contraprova item a item)

| Onde | Alegação | Estado real (hoje) | Veredito |
|---|---|---|---|
| Rotas | 71 / 76 / 95 | **110** (url_map) | ✔ números velhos |
| Skills | 18 / 39 / 47 / 50 / 55 | **55 builtin** | ✔ (55 é o atual) |
| Testes | 88 / 241 / 251 | **261** | ✔ |
| Tools | 34 / 35 / 36 | **37** | ✔ |
| DOCUMENTACAO | "40 releases" vs 103 tags; v4.0/v4.1 duplicadas | confirmado (doc de época) | ✔ |
| docs.md | "Versão 2.0.0"; auth `Bearer` | confirmado; código aceita `X-Pluto-Token`/`?token=`/json — **não Bearer** | ✔ docs.md errado |
| MAPA_APLICACAO | "gerado na v3.14.2" c/ conteúdo v8.6; "MÁQUA", "inejociáveis", "troças" | confirmado nas linhas 5, 36, 70, 146 | ✔ |
| ROADMAP-V9 | "SYSTEM_PROMT" | **não existe** no arquivo atual | ✖ |
| ROADMAP-V9 | "quador" (381), "avali" (345) | confirmado | ✔ typos |
| ROADMAP-V9 | convez-ai "não existe" × "não achei" | a MESMA linha 111 diz ambos — semanticamente consistente | ✖ |
| MAPA-FLUXOS §10 | P6 "⏳ T248" apesar de entregue | a conferir na revisão do MAPA (§4.10) | 🔎 |
| DIRETRIZES | numeração 1,2,3,6,6,7 | **corrigida na P8.3** (1–6 + nota histórica "Diretriz 7"=6) | ✖ |
| CHECKLIST | 4 achados × 6 do ROADMAP | contagem depende da grafia ("achado de campo" × "º achado") | ⚠ |
| README | branches param na v8.1.0 (linha 678) | confirmado | ✔ |
| README | tabela de API lista 8 de ~95 | pior: são **8 de 110** | ✔ |
| README | duas seções de instalação | 1 bloco rápido (§61) + universal (§76) — estrutura intencional, menções espalhadas | ⚠ cosmético |
| README | `pluto memoria` × `pluto memory` | **não achei** "pluto memoria" no README atual | ✖ |

**Causa comum aceita:** números à mão em ~12 docs + gen_doc.py
misturando prosa velha. Solução em §4.10.

---

## §4 — Melhorias propostas: triagem

| # | Melhoria | Decisão | Quando |
|---|---|---|---|
| 1 | Sensibilidade por ferramenta (D2 estendido a dado pessoal) | **ACEITA — prioridade 1 de segurança** | junto ao lote 5 do P0.1 |
| 2 | Fechar o servidor local (Host/Origin, bind, segredo por webhook no header, teste url_map) | **ACEITA — prioridade 2** | junto ao lote 5 |
| 3 | Saída de web/e-mail/MCP = não confiável; egress com aprovação; guard sem auto-exec | **ACEITA** | lote 5/6 |
| 4 | T107 antes da tag ✖ (já feito) · keyring/ACL no win · SHA256SUMS + deps no update | **ACEITA** (partes pendentes) | release v9.0.0 |
| 5 | Job noturno com modelo real (cenários de ouro) | **ACEITA** (DoD#6) | pós-P0.1, pré-tag |
| 6 | `format:"json"`/schema do Ollama nos veredictos · `prompt_eval_count` | **ACEITA** | P0.2 |
| 7 | Ampliar CI: ARM64 · eixo Python (✖ já existe) · mínimo 3.11 · pip-audit · secret scanning · dividir suíte | **ACEITA** (parcialmente feito) | release + pós |
| 8 | Renomear confiança → cobertura de evidência + calibração | **ACEITA** | P0.2 |
| 9 | Medir perfil (mini-benchmark) em vez de nome | ACEITA (backlog) | pós-v9 |
| 10 | MCP: header `MCP-Protocol-Version` + SSE como legado | **ACEITA** | P0.2 |
| 11 | Docs fonte única: gen_doc preenche contagens entre marcadores + teste de divergência + mover docs velhos p/ `docs/historico/` (ficam vivos README, MAPA-FLUXOS, GUIA) | **ACEITA** | junto ao §5 |
| 12 | Medir Waitress com 5 abas; subir threads (✖ já 16) / limitar streams | ACEITA (backlog) | pós-v9 |

---

## §5 — Plano de cobertura 89% (mandato deste documento)

### 5.1 Baseline MEDIDO em 11/11/2026 — 68%
`coverage run --source=pluto tests/run_all.py` (suíte 261/261):
**14.273 stmts · 4.615 miss · 68%** — relatório completo em
`docs/COBERTURA-BASELINE-2026-11-11.txt`. (O backlog dizia "≥70% no
CI" como meta a medir: estamos a 2 pontos dela, sem nunca ter
medido.)

**Maiores buracos (miss):** cli.py 593 · server/app.py 487 ·
manager.py 222 · emailcfg.py 181 · ollama_client.py 113 ·
selftest.py 107 · omniroute.py 101 · agent.py 97 · financas.py 93 ·
daemon.py 72 · telegram_gw.py 72 · tui.py 120 · stt.py 33 (0%).

### 5.2 A contas do 89%
89% de 14.273 = **12.703 stmts cobertos** → tolera **≤ 1.570 miss**.
Hoje faltam **3.045**. Sem exclusões malandras: `__main__` (3 stmts)
é a única exclusão declarável; tudo else conta.

### 5.3 Fases (cada uma fecha com CI verde nos 4 jobs)

| Fase | Alvo | Como | Recupera (miss→) |
|---|---|---|---|
| **F0 — hoje** | **gate no CI: floor 66%** | passo novo no job ubuntu-3.13: `coverage run` + `coverage report --fail-under=66` (não regredir nunca) | — |
| **F1** | **75%** | módulos 0–46%: bateria de subcomandos do **cli.py** via `build_parser()` (o maior buraco, 593); manager/daemon com subprocess falsos; stt/tui com fakes | ~1.000 |
| **F2** | **82%** | **server/app.py**: teste que percorre as **110 rotas** do `url_map` (auth + smoke GET/POST) — mata o buraco de 487 E o item §1.3 do auditor; emailcfg/ollama_client/telegram com os fakes IMAP/SMTP que a suíte já tem | ~1.000 |
| **F3** | **89%** | selftest/omniroute/code_manager/whatsapp/agendacfg/conversations/skills/scheduler; fechamento das pontas em tools/orchestrator | ~1.050 |

**Definition of Done do 89%:** `coverage report --fail-under=89` verde
no CI (ubuntu 3.13) + os 4 jobs da matriz verdes + suíte intacta
(261+ novos casos, nenhum pulado novo) + ruff limpo.

### 5.4 Regras do jogo
1. **Cobertura conta comportamento, não linha por linha**: cada caso
   novo precisa afirmar um contrato (a cultura da casa: asserção com
   diagnóstico, msgs de erro são contrato);
2. nenhum teste pode ficar **pulado** em SO algum (o P0.1 fecha isso
   antes da tag — faltam E+F+G, 16 no win);
3. fakes continuam legítimos para integração (IMAP/SMTP/binários),
   mas o **job noturno com modelo real** (§4.5) cobre a classe que
   mock não vê — as duas camadas juntas é que valem;
4. o gate **só sobe, nunca desce** (ratchet): floor = máximo já
   alcançado −2 pontos de folga.

### 5.5 Interação com o que já está em curso
- **P0.1 lote 5 (E+F) e lote 6 (G)** fecham a portabilidade ANTES da
  tag — pré-requisito do F1 (nenhum pulado);
- as melhorias **§4.1–4.3 (segurança)** entram junto ao lote 5: o
  teste do `url_map` é o mesmo do F2;
- **release v9.0.0**: tag com gate F0 no CI + backlog declarado
  (89% = meta F3, pós-tag, sem mentir no README).

---

*docs/VALIDACAO-PONTO-A-PONTO-V9.md · 11/11/2026 · contraprova
executada contra o repo no commit 09068f6 (CI 43031210782 verde nos
4 jobs). Fonte da auditoria: análise externa dos 12 documentos.*
