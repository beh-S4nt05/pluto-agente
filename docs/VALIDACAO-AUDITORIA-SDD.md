# Validação da Auditoria de Conformidade SDD — pluto-agente

> Contraparte da `Auditoria de conformidade SDD pluto-agente.md` (auditoria
> externa, 10/11/2026, commit `97d81e7`). Cada claim foi **validado contra
> o código real** — reproduzindo por execução quando possível (Diretriz 7:
> sucesso só com prova; vale contra a auditoria também).
>
> **Veredito: auditoria de alta qualidade e honesta.** 3/3 achados Alta
> CONFIRMADOS (2 com PoC reproduzido), 9/9 Média confirmados (1 com
> imprecisão menor), 2 imprecisões pequenas, 0 erros materiais. Ela também
> corrigiu uma checagem apressada minha (ver V-10). Os 3 achados Alta
> **bloqueiam a tag v9.0.0** — aceito o plano de ação dela.

## 1. Achados Alta — validação

| ID | Claim da auditoria | Status | Evidência da validação |
|----|-------------------|--------|------------------------|
| A1 | Estágios 4/6/7 não são impostos pelo pipeline; `verificar()`/`avaliar()`/checkpoint só existem via tool escolhida pelo modelo | **CONFIRMADO** | `grep` em `orchestrator.py`, `agent.py`, `server/app.py`: **zero** chamadas; a instrução vive nas DESCRIPTIONS das tools (decisão documentada no T245 §12 pelo orçamento <6000 do prompt). T244/T245/T246: `run_pipeline` nunca exercitado. A SPEC §4 ("arquitetura, não opção") **superestata** o que o código impõe |
| A2 | `git_run` sem denylist: `core.fsmonitor` executa comando; `diff --output` escreve fora | **CONFIRMADO COM PROVA** | **PoC 1 reproduzido**: `git config core.fsmonitor 'touch /tmp/pluto-poc-pwned'` + `git status` → arquivo criado (comando executado). **PoC 2 reproduzido**: `git diff --output=/tmp/pluto-poc-diff` → diff escrito fora do workspace. Condição real: hosts sem bwrap (macOS/Windows). O allowlist `_GIT_OK` + bloqueio `--global/--system` não cobrem nem `config` local perigoso nem opções de `diff` |
| A3 | Secretário sem DLP: briefing/lembretes vazam remetente/assunto/agenda/diário; SPEC se contradiz (RF-SEC-01 × NFR-01) | **CONFIRMADO** | `secretario.py`: **0** chamadas a `mascarar()`; `vida.py`: 3 (o padrão correto já existia). NFR-01 ("DLP em todo caminho externo") × RF-SEC-01 (briefing com e-mails/agenda) — contradição real da SPEC |

## 2. Achados Média — validação

| ID | Claim | Status | Evidência |
|----|-------|--------|-----------|
| M4 | `_SENSITIVE_READ` fixo em `~/.pluto/secrets`; data-dir custom → segredo lido; `~/.ssh` aceito como escopo | **CONFIRMADO COM PROVA** | PoC: `Config(data_dir=~/pluto-poc-audit)` → `read_file secrets/telegram.key` retornou `TOKEN-SECRETO-PoC` (ok=True). `validar_escopo_projeto("~/.ssh")` → ACEITO (só recusa home inteira, `_SCOPE_DENY` de sistema e `cfg.data_dir`) |
| M5 | Hook pré-push não existe | **CONFIRMADO** | `grep pre-push/pre_push/instalar-hook` em `pluto/` e `.github/` → vazio. SPEC §2.5 é convenção, não mecanismo |
| M6 | Escritas não atômicas; `_salvar_registro` engole OSError → briefing em loop de 15 s | **CONFIRMADO** | `secretario.py:61-62 e 79-80`: `except OSError: pass` (2×). `config.py:209`, `conversations.py:163` (current.json), `notify.py:33,59`: `write_text` direto. Contagem: 13 módulos com replace × 53 `write_text` (auditoria: 14×~55 — mesma magnitude) |
| M7 | `ok` inferido por prefixo `ERRO`/`BLOQUEADO`; `✖` conta como ok=True | **CONFIRMADO** | `tools.py`: `ok = not output.startswith(("ERRO", "BLOQUEADO"))`. Afeta ≥7 retornos `✖` — **incluindo a tool `projeto` do P8 (nossa)** |
| M8 | Só 6/55 skills têm `## Exemplo`; graduação sem efeito prático | **CONFIRMADO** | `grep -l "## Exemplo" skills/*/SKILL.md` → 6. RF-SKL-01 da SPEC generaliza demais (o `## Exemplo` era requisito das skills V9/P5) |
| M9 | 3 portões sem consumidor; `solicitar_escalada` sem chamador; heurística por substring | **CONFIRMADO COM PROVA** | `ctx_longo`/`autonomia_estendida`: 0 consumidores fora de `capacidades.py`. `solicitar_escalada`: 0 chamadores. `_FORTE` contém `'pro'` → **reproduzido**: `improved-chat`, `promptist-7b`, `gpt-4o-mini`, `o3-mini`, `claude-haiku` → todos "forte" |
| M10 | Dívida = 39 únicos (não 43); T41/T142/T188 no Windows, T107 no macOS | **CONFIRMADO (e corrigiu a MIM)** | win=38, mac=5, **únicos=39**, repetidos=4. Pulados incluem `T41_secrets_protegidos_contra_o_agente`, `T142_telegram_token_allowlist_e_comandos`, `T188_nunca_mudo_e_dados_reais` (win+mac), `T107_detectar_pasta_do_projeto` (mac). Minha 1ª checagem usou prefixo (`"T41" in set`) contra nomes completos → falso negativo; a auditoria estava certa |
| M11 | Versão 8.6.0; README 241 testes; CHANGELOG zero v9; waitress ausente; CI só 3.13; pyproject ≥3.9 | **CONFIRMADO** | `config.VERSION="8.6.0"` · `pyproject 8.6.0` · README "**v8.6.0** · 241 testes" · CHANGELOG head v8.6.0 · `requirements.txt` sem waitress · `ci.yml python-version "3.13"` · `requires-python ">=3.9"` |
| M12 | Diretrizes/Roadmap/Mapa fora do repo; numeração das diretrizes quebrada | **CONFIRMADO** | `DIRETRIZES.md`, `ROADMAP-V9-SECRETARIO.md`, `MAPA-FLUXOS-V9.md` existem só em `/home/user` (fora do repo). `DIRETRIZES.md`: dois itens "6", nenhum 4/5 |

## 3. Baixa e demais seções

| Claim | Status | Evidência |
|-------|--------|-----------|
| §3: 12 módulos sem RF = 1.837 LOC | **CONFIRMADO** | `wc -l` dos 12 módulos = 1.837 exato |
| §3: dados persistidos fora do §6 (secretario.json, lembretes.json, session_goals.json, dossies/…) | **CONFIRMADO** | Presentes em `secretario.py`, `orchestrator.py`, `vida.py`, `dossie.py` |
| §4: CI 19 runs → 12 ✔ / 7 ✖ | **CONFIRMADO** | API GitHub: exatamente `{'success': 12, 'failure': 7}` |
| §1: suíte 253/253, 37 tools, 55 skills, prompt ~5254/6000 | **CONSISTENTE** | Bate com nossos runs (prompt varia por query/host — 5223–5607) |
| §4: cobertura 67,4% e por módulo | **NÃO REPRODUZIDO** | Medição da auditoria (não re-medi; plausível pela estrutura da suíte) |
| §4: chmod 600 pós-escrita/inerte no Windows | **NÃO REPRODUZIDO** | Plausível pela leitura; sem PoC meu |
| macOS/Windows ao vivo | **NÃO REPRODUZIDO** | Valido pelo CI (macos/windows verdes) — limitação declarada por ambas as partes |

## 4. Imprecisões encontradas NA auditoria (menores)

1. **"T244/T245/T246 com 0 chamadas a Agent"** — T245 instancia `Agent` 1×
   (§12 do teste) para inspecionar o `system_prompt`; não exerce o pipeline.
   Imprecisão literal, espírito correto (`run_pipeline` = 0 em todos).
2. **"14 módulos com tmp+replace"** — contei 13 (diferença de critério de
   contagem; magnitude idêntica).

Nenhuma das duas muda conclusão ou severidade.

## 5. Veredito e decisão

- **Auditoria aprovada como insumo de correção** — precisão alta, honesta
  (declara o que não verificou), e pegou um erro da MINHA validação apressada
  (M10), que corrijo publicamente aqui.
- **Os 3 achados Alta são bloqueadores da tag v9.0.0** — concordo com o
  plano de ação da própria auditoria (§5 dela), adotado como **P8.1**:
  1. Estágios 4/6/7 impostos em `run_pipeline` (+ teste que falte se o
     quadro/rodapé faltar na entrega) — ou SPEC §4 reescrita; decisão: impor
     no pipeline (pedido nº 3 do operador).
  2. `git_run` endurecido (blocklist de `config`: `core.fsmonitor`,
     `core.sshCommand`, `core.hooksPath`, `core.pager`, `core.editor`,
     `alias.*`; bloquear `--output*` em diff/log; PoCs → regressão).
  3. `mascarar()` no briefing/lembretes + RF-SEC-01 reescrita (o que pode
     sair) — fim da contradição com NFR-01.
- Sequência seguinte: M4/M7/M6/M5 (segurança/robustez) → docs (diretrizes
  no repo, CHANGELOG v9, README, bump) → **P0.1** (39 únicos, prioridade
  T41/T142/T188-win e T107-mac) → release v9.0.0.

*docs/VALIDACAO-AUDITORIA-SDD.md · 10/11/2026 · validação executada sobre
`97d81e7` (main) · suíte 253/253 · CI do HEAD verde nos 3 SOs.*


---

## 6. Atualização (10/11/2026) — P8.1 ENTREGUE

Os 3 achados Alta foram corrigidos e provados por regressão:
- **A1 → T254**: estágios 4/6/7 impostos no `run_pipeline`
  (missão herda); entrega de task sai com verificação + quadro;
  conversa segue leve. 256/256, zero teste existente quebrou.
- **A2 → T255**: `git_run` com denylist na tool (chaves de config
  que executam comandos + `--output`); PoCs viraram regressão.
- **A3 → T256**: DLP no envio do secretário — e o teste EXPOS uma
  lacuna extra: o DLP global só mascarava domínios pessoais;
  remetente corporativo agora também é mascarado no canal.

Próximos da lista da auditoria: M4 (secrets por data-dir), M7
(inferência de `ok`), M6 (escritas atômicas), M5 (hook pré-push)
→ docs → P0.1 → release.
