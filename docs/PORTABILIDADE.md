# 🧭 PORTABILIDADE — dívida rastreada da suíte (Windows · macOS)

> **Contexto:** a suíte rodou pela 1ª vez em Windows e macOS no dia
> 07/11/2026, pelo CI recém-criado da V9.0.0 (run 42340204729, commit
> 96fa483). Em 103 tags manuais ela só tinha rodado em Linux — o CI
> expôs **43 testes** que assumem POSIX (38 no Windows, 5 no macOS).
>
> **Filosofia:** o mesmo "degradação honesta" do produto. Nenhum teste
> falha em silêncio e nenhum é escondido: os não-portados pulam
> **contados** (linha `RESULTADO: … · N pulado(s)`) e estão listados em
> `_NAO_PORTADOS` no `tests/run_all.py`. **Queimar a dívida = corrigir
> e remover da lista**; o CI nas 3 plataformas é a prova.

## Como portar (receita)

1. Corrija o teste (ou o produto, quando o defeito é real — ver tabela);
2. remova o nome de `_NAO_PORTADOS` em `tests/run_all.py`;
3. `pluto gates` local + push → o CI revalida nos 3 SOs.

O runner tem um guarda: nome na lista que não existe mais na suíte
**falha o pipeline** (dívida com nome de teste apagado = lista mentindo).

## Windows — 16 testes (era 38 — A ✔ lote 2 · B ✔ lote 3 · C+D ✔ lote 4, 10/11/2026)

Causas confirmadas na 1ª execução (log do job), agrupadas:

### A. Binários fake não executáveis — ✔ PORTADO (P0.1 · lote 2, 10/11/2026)
O Windows só executa PE (.exe/.cmd/.bat); os fakes da suíte eram
scripts sh (`WinError 193`). **5 testes destravados:**
~~T164~~ · ~~T165~~ · ~~T170~~ · ~~T171~~ · ~~T227~~.

Fakes agora são gerados por SO (`_fixture_mm`, `_fixture_n8n_fake`,
T170): no Windows viram `.cmd` — ponte para um script Python quando a
saída importa (UTF-8 controlado), batch direto quando é ASCII
(`@echo v24.1.0`), e `n8n.cmd` vivo via `ping` (o npm real também
instala `n8n.cmd`, não o script sh).

**Bugs de PRODUTO achados pela porta (todos corrigidos):**
- `procs.start`: `start_new_session=True` fixo → `ValueError` no
  Windows (agora `plataforma.popen_destacado_kwargs()`);
- `procs.stop`: `os.killpg`/`os.getpgid` não existem no Windows
  (`AttributeError` não capturado) → ramo Windows via `plataforma.matar`;
- `plataforma.matar`: `taskkill /T` (árvore — filhos do wrapper
  `.cmd` não ficam órfãos);
- `fluxos.n8n_bin`: retorna `n8n.cmd` no Windows (shim real do npm);
- `multimodal.transcrever`: UTF-8 explícito nos subprocess (o
  whisper.cpp emite UTF-8 em todo SO; `text=True` sem encoding
  decodava cp1252 no Windows → mojibake).

A prova de vida do T171 usa `plataforma.liveness` — nunca
`os.kill(pid, 0)`, que no Windows TERMINA o processo.

### B. Caminhos POSIX / backslash — ✔ PORTADO (P0.1 · lote 3, 10/11/2026)
**11 testes destravados:** ~~T17~~ · ~~T29~~ · ~~T41~~ · ~~T108~~ ·
~~T109~~ · ~~T116~~ · ~~T120~~ · ~~T151~~ · ~~T197~~ · ~~T202~~ · ~~T209~~
(T116 fechou no 2º commit do lote — o diagnóstico adicionado na 1ª
tentativa apontou o bug exato no log do CI).

Causas reais (log do run 42340204729) e o que foi feito:

| Causa | Correção |
|---|---|
| `_PROJETO_RE` (orquestrador) só casava `~/…` e `/…` — caminho `C:\…` citado pelo operador NUNCA era detectado → sem escopo de projeto (T109 · T120 · T197) | 🐛 produto: ramo de drive no regex + exemplos do SO na pergunta de caminho |
| `_MENCAO_RE` sem `:`/`\` — `@C:\Users\…` virava menção `'C'` (T202 · T209) | 🐛 produto: ramo de drive ANTES do genérico (o genérico casava 'C' e parava) + `~` no meio (8.3 `RUNNER~1`) |
| `CLAUDE_LIGHT_PROMPT` com LF no argv — shim `.cmd` (npm) corta no 1º LF (T17) | 🐛 produto: diretiva single-line |
| `_SCOPE_DENY` POSIX-only — com drive-paths detectados, `C:\Windows` passaria | 🐛 produto: entradas Windows no deny (fecha o buraco aberto pelo novo ramo) |
| `st_mode == 0o600` (T41) | teste OS-aware: POSIX exige 600; no Windows a proteção é a ACL do perfil (porta ACL = backlog do release) |
| `"/tmp"` como dir de watch (T29) | `tempfile.gettempdir()` |
| `pwd` (T108) | `cd` no Windows |
| `str(relative_to())` com backslash (T151) | `.as_posix()` |
| T116 | 🐛 produto (achado no CI do lote 3): `read_skill_md` validava com `startswith(str(base) + "/")` — barra LITERAL; no Windows o separador é `\` → `PermissionError` engolida pelo `except` → **nenhuma skill virava MANUAL DA TAREFA** (delegação morta em silêncio). Corrigido com `Path.is_relative_to` |

### C. Prompts e fixtures com exemplo POSIX — ✔ PORTADO (P0.1 · lote 4)
~~T113~~ · ~~T121~~ — os dois já estavam destravados pelo fix do
`_PROJETO_RE` do lote 3 (o sintoma — orçamento padrão em vez de 8
passes/40 tools — era a não-detecção do caminho `C:\…`); o lote 4
só tirou da lista e provou no CI. (T120 saiu no lote 3.)

### D. Autostart / SO — ✔ PORTADO (P0.1 · lote 4)
~~T98~~ · ~~T166~~ · ~~T174~~ · ~~T188~~ (os dois últimos fecharam a
dívida do **macOS** junto).

> ~~P0.1 lote 1: `_SCOPE_DENY` POSIX-cêntrico~~ — **RESOLVIDO no lote
> 3**: entradas Windows (`C:\Windows`, `C:\Program Files`,
> `C:\ProgramData`…) no deny. Outras UNIDADES (D:\, E:\…) seguem
> cobertas pelo deny resolvido por unidade quando o caminho existe.

| Teste | Causa real | Correção |
|---|---|---|
| T98 | o digesto pina 4 seções canônicas (`top RAM`, `uptime e carga`…) que só existiam na tabela Linux | 🐛 produto: `_DIAG_WIN` ganha `top RAM` (Get-Process por WS) e `uptime e carga` (LastBootUpTime/LoadPercentage); `_DIAG_MAC` ganha `top RAM` (`ps aux -m`) — todas powershell no win (T173) |
| T166 | teste pina `apt install`; o produto dá o hint DO SO (winget/brew) — comportamento correto | teste OS-aware (apt/brew/winget) |
| T174 | fluxo REAL do teste era systemd-only (`status.so == "linux"`) | teste OS-aware: linux systemd · macos launchd (launchctl) · windows .bat na Inicialização — todos com HOME falso + subprocess falso |
| T188 | marcador de CPU real (`Model name` do lscpu) é Linux-only | marcadores por SO: lscpu · sysctl (`brand_string`/`hw.physicalcpu`) · Get-CimInstance (`NumberOfCores`…) |

### E. Guards do Claude Code (2)
T38_guard_retry_modelo_recupera_e_executa · T39_guard_teimoso_hermes_executa_no_lugar
— mensagens/fluxo com `claude` ausente diferem no Windows.

### F. Update/instalação (3)
T81_update_end_to_end_v3110_local (`não consegui consultar o GitHub`) ·
T177_update_garante_comando_betterme · T178_instalacao_editavel_robusta.

### G. Demais (11) — triar na 1ª porta
T55 · T65 · T124 · T141 · T142 · T172 · T183 · T192 · T213 · T216 · T236.

## macOS — **ZERO dívida** (P0.1 · lote 4, 10/11/2026)

| Teste | Como saiu |
|---|---|
| ~~T107_detectar_pasta_do_projeto~~ | ✔ lote 1 — deny nos DOIS planos (`/etc`→`/private/etc`) |
| ~~T98_diagnostico_em_uma_chamada~~ | ✔ lote 4 — `top RAM` no `_DIAG_MAC` (seções canônicas) + marcador sysctl |
| ~~T166_sem_binario_nao_quebra_e_orienta~~ | ✔ lote 4 — hint `brew install` (o produto já orientava certo) |
| ~~T174_boot_autostart_nos_tres_sos~~ | ✔ lote 4 — fluxo launchd provado (plist + launchctl, HOME falso) |
| ~~T188_nunca_mudo_e_dados_reais~~ | ✔ lote 4 — marcador de CPU por SO |

A suíte agora roda **261/261 no macOS** (nenhum pulado).

## Prioridade sugerida

1. ~~**T107 (macOS)**~~ ✔ lote 1 — bug de segurança do deny-list;
2. ~~Grupo A do Windows~~ ✔ lote 2 — WinError 193 + 5 bugs de produto;
3. ~~Grupo B do Windows~~ ✔ lote 3 — 11 testes + 5 bugs de produto;
4. ~~Grupo C+D~~ ✔ lote 4 — macOS em ZERO; win 22→16;
5. Resto: E-guards (2) · F-update (3) · G-triagem (11).

*docs/PORTABILIDADE.md · V9.0.0 P0 · fonte: run 42340204729 (logs dos
jobs windows-latest/macos-latest, 07/11/2026). Atualizar a cada porta.*


## Python (P8.3 — auditoria M11)

- `pyproject.toml` declara `>=3.9` (análise estática).
- O CI cobre **3.13** nos 3 SOs e **3.11** no Linux (matriz da P8.3).
- 3.9/3.10: declarados como análise estática — sem CI. Se uma
  dessas quebrar, o fix vem com regressão na suíte.
