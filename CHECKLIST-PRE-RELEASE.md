# ✅ Checklist pré-release — Pluto

> Lição dos 4 achados de campo (#1 entry points, #2 PEP 660, #3
> performance, #4 agente mude/alucinado): **testes de happy path verde
> ≠ app que cumpre a função.** Este checklist é GATE — nenhum `git tag`
> sai sem todos os itens fechados. Desde a v9.0.0 ele também é pino da
> suíte de coerência: a SPEC (§9) e o T261 cobram que ele exista e
> acompanhe a release.

## 1. Promessas ↔ testes
- [ ] Toda promessa do **GUIA-DE-USO/README** tem caso de teste
      correspondente (ou a promessa sai do guia). Promessa sem teste
      é dívida.
- [ ] **Versão coerente em TODOS os lugares** (T261): `config.VERSION`
      == `pyproject.toml` == header do CHANGELOG == README == MAPA —
      e **sem sufixo dev** (`9.0.0`, não `9.0.0-dev`).

## 2. Modos de falha ANTES do happy path
- [ ] Para cada superfície user-facing (chat, tarefas, gateways, GUI):
      o que acontece se o pipeline devolve **vazio**? se a **thread
      morre**? se dá **timeout**? Cada um desses tem teste (padrão T188).
- [ ] Nenhum fluxo termina em **silêncio**: sempre `done` ou `error`.

## 3. Campo → regressão
- [ ] Todo transcript/erro reportado pelo operador vira caso de
      regressão permanente ANTES do próximo tag (#1→fix, #2→fix,
      #3→T180, #4→T188).

## 4. Bateria real (comportamental)
- [ ] Suíte integral em mock: **N/N com 0 pulados nos 3 SOs** (CI nos
      4 jobs — ubuntu 3.11/3.13, windows, macos; o RESULTADO de cada
      job no log é a prova). Mock é roteiro determinístico: não valida
      comportamento de modelo.
- [ ] **Na máquina do operador (com Ollama de pé):** `pluto selftest`
      verde + 1 jornada real por superfície prometida (ex.: "relatório
      do PC" → tool de diagnóstico + dados reais no arquivo) antes de
      declarar "pronto". É o DoD#6 do ROADMAP §4 — **não é simulável**.

## 5. Qualidade e release
- [ ] ruff `E9,F,B,PLE` limpo · `pluto varredura --tudo` sem críticos ·
      `gen_doc.py` regenerado (depois de CHANGELOG/VERSION).
- [ ] **Gate de cobertura F0** (RF-INF-06): `coverage run --source=pluto
      tests/run_all.py` + `coverage report --fail-under=<floor>` verde —
      floor do ratchet = máximo já alcançado −2 pts (66% na v9.0.0;
      **só sobe, nunca desce**).
- [ ] CI verde nos **4 jobs** no commit da tag (a tag roda os MESMOS
      portões no release.yml antes de publicar o zip).
- [ ] Tag anotada `vX.Y.Z` com mensagem de marco · push · release.yml
      publica zip (`git archive`, só rastreado) + notes · demo com
      curl de verificação.

## 6. Honradez (Diretriz 7)
- [ ] Backlog declarado, não escondido (README/CHANGELOG/SPEC §8).
- [ ] DoD com status REAL: pendente é estado válido, sucesso fingido
      não. O que é campo do operador está MARCADO como campo.
- [ ] Nada de número novo sem prova no log (CI run id citado).

---

## Registro de execução — v9.0.0 (12/11/2026)

- §1 ✔ T261 pin a coerência (config+pyproject+CHANGELOG+README, sem
  dev) · §2 ✔ herdado da suíte (T188 e família) · §3 ✔ P0.1 consumiu
  as evidências de campo da auditoria de portabilidade.
- §4 ✔ suíte: **262/262 · 0 pulados** nos 3 SOs — CI 43302014806
  (a10f2b5, 4/4 jobs; RESULTADO conferido no log de cada job).
  **§4 campo (DoD#6) ⏳ ABERTO**: 1 dia de uso com Ollama + `pluto
  selftest` na máquina do operador — harness pronto, campo não
  simulável (declarado no CHANGELOG/ROADMAP §4/SPEC §8).
- §5 ✔ ruff · varredura · gen_doc regenerado · **gate F0 floor 66%**
  (baseline medido 68% em 11/11 — docs/COBERTURA-BASELINE-2026-11-11.txt)
  · CI verde no commit da tag · tag v9.0.0 anotada · release.yml
  publica zip + notes curadas (docs/RELEASE-NOTES-v9.0.0.md).
- §6 ✔ backlog declarado: F1 75% → F2 82% → F3 89% (§5 da validação
  ponto a ponto) · ACL/keyring Windows · P0.2 (§4 da auditoria nº 2).
