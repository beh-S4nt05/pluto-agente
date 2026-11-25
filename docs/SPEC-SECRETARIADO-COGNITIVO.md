# Secretariado cognitivo — especificação de evolução (proposta SDD)

Status: proposta para revisão; não representa funcionalidades entregues. Base: main, 271f172 (PR #18). A SPEC.md e POLITICAS.md permanecem normativas; mudanças de comportamento exigem atualização simultânea da SPEC e testes.

## Identidade e limites
Pluto é um secretário pessoal digital multifacetado, proativo, adaptativo, multimodal e local-first, que compreende, organiza, planeja, executa, supervisiona e audita responsabilidades pessoais, acadêmicas, profissionais e técnicas sob autoridade do operador. Servidor permanente é um perfil de implantação, não uma identidade nem pré-requisito de uso. Um cérebro coordenador e especialistas como ferramentas (ADR-001). Sem microserviços obrigatórios, sem novo gateway obrigatório, sem reescrita de Python, sem duplicação da memória ou do scheduler. Código e segredos permanecem locais (D2); escalação externa exige autorização conforme SPEC. Conteúdo externo é dado não confiável, nunca autoridade.

## Arquitetura alvo
Monólito modular com portas/adaptadores e núcleo determinístico: canais -> ingestão de eventos -> contexto e responsabilidades -> política/prioridade -> plano -> orquestrador -> ferramentas/especialistas -> verificação -> auditoria/aprendizado. Scheduler e daemon acionam o mesmo núcleo, sem loops concorrentes duplicados. LLM propõe; código valida e autoriza; ferramenta executa; evidência determina resultado. Domínios compartilham identidade e políticas, com escopos isolados: executivo, pessoal, acadêmico, financeiro, profissional, comunicação, pesquisa, biblioteca, engenharia, automação, administração de sistemas e auditoria. Domínios são perfis de capacidades, não novos agentes obrigatórios.

## Contratos propostos
- Evento: id, origem, tipo, timestamp UTC, referência de payload local, classificação de sensibilidade, chave de deduplicação. Não persistir segredo no evento.
- Responsabilidade: id, domínio, objetivo, origem, prazo opcional, prioridade, estado, dependências, autorização, próximo passo, evidência, revisão, versão.
- Estados: pendente -> planejada -> aguardando autorização / pronta -> executando -> verificando -> concluída / falha / bloqueada; cancelada por operador. Conclusão exige evidência; tentativa ambígua de efeito externo exige reconciliação, nunca retry cego.
- Autorização: escopo de ação/recurso, prazo, limite de gasto, revogação, versão da política. Default deny para efeitos externos não autorizados. Níveis existentes de autonomy.py continuam compatíveis; autonomia por ação complementa, não substitui hard gates. Sem transações financeiras, exclusões irreversíveis, alteração de segurança, escalada de dados ou envio não autorizado.
- Proatividade: eventos e regras determinísticas geram propostas deduplicadas, com janela de silêncio, prioridade, frequência máxima e opt-out. Sem LLM em polling ocioso. Não confundir inferência com fato.
- Persistência: avaliar SQLite stdlib para estados, eventos, leases e outbox transacionais; migração versionada, backup e rollback, manter arquivos existentes como fontes até migração explícita. Um executor por lease; expiração e reconciliação; idempotência por efeito. Sem alegação de exactly-once em APIs externas.
- Memória: Obsidian Markdown como camada legível, índice local derivado e proveniência; grafo de código AST existente não é Graphify completo. Avaliar Graphify opcional por adaptador, sem duplicar fonte de verdade. Atualização, conflito, exclusão e reindexação verificáveis.
- Inteligência: estender llm_providers.py e autoselect.py, aproveitar metrics.py e certeza.py. OpenRouter já registrado; NanoGPT novo adaptador após validar contrato oficial. Registrar uso real de entrada/saída, unidade de franquia, reset e multiplicador por provedor; desconhecido não é zero. Reserva atômica antes de chamada paga, teto configurável de R$180/mês incluindo tarifas e margem cambial, sem compra automática. Benchmark por tarefa, qualidade/latência/custo; fallback local obrigatório conforme D2; sem transmitir código para avaliação remota.
- Implantação: desktop e serviço persistente opcionais; interfaces existentes; acesso remoto desabilitado por padrão, autenticação e transporte seguro antes de expor; heartbeat, recuperação, backup restaurável e limites de RAM/CPU/disco. Dispositivo Linux dedicado é opcional.
- Automação: evoluir fluxo/fluxos/recipes/scheduler; motor nativo com DAG validado, dependências, checkpoints, timeout, cancelamento, tentativas limitadas, reconciliação e logs; n8n permanece adaptador opcional.
- Aprendizado: learning.py registra lições com evidências; alterações estruturais e de política requerem aprovação. Benchmark e cache não podem promover resultado não verificado.

## Matriz de rastreabilidade e aceitação
| ID | Requisito | Base existente | Evidência exigida |
|---|---|---|---|
| SEC-01 | Responsabilidades persistentes | secretario, mission, scheduler, dossie | Criar, priorizar, retomar após reinício e concluir só com prova |
| SEC-02 | Proatividade controlada | secretario.tick, daemon | Evento duplicado gera uma proposta; silêncio e revogação respeitados |
| SEC-03 | Autonomia granular | autonomy, contratos, tools | Aprovação expirada/revogada bloqueia efeito; D2 prevalece |
| SEC-04 | Execução resiliente | orchestrator, mission, scheduler | Crash antes/depois de efeito externo; reconciliação sem duplicar |
| SEC-05 | Conhecimento longitudinal | memory, vault, knowledge, grafo | Recuperação com origem, conflito explícito e reindexação |
| SEC-06 | Multi-LLM e orçamento | llm_providers, autoselect, metrics, certeza | 429, timeout, reset, concorrência e saldo insuficiente; nenhum gasto acima do limite reservado |
| SEC-07 | Automação nativa | fluxo, fluxos, recipes | Workflow com dependências, falha, retomada e cancelamento sem n8n |
| SEC-08 | Domínios multifacetados | skills, specialists, secretario, financas, notebook | Cenários reais acadêmico, pessoal, profissional e técnico; sem escalada de privilégio |
| SEC-09 | Operação contínua opcional | daemon, supervisor, boot, server | Reinício, backup/restauração, autenticação, degradação offline |
| SEC-10 | Aprendizado verificável | learning, metrics, arena | Comparação antes/depois com conjunto fixo; aprovação de mudança |
| SEC-11 | Auditoria transversal | audit, verificacao, autoavaliacao | Correlação evento->decisão->ação->evidência; logs sem segredos |
| SEC-12 | Segurança de entradas | tools, MCP, web, email | Injeção indireta não autoriza egress; regressões dos PRs anteriores |

Todos os requisitos acima estão em estado **a validar**, ainda que possuam componentes existentes. Não inferir cobertura pelo número de testes.

## Sequência de PRs (cada um reversível, sem merge automático)
1. P0: inventário de contratos e chamadas reais, matriz requisito/código/teste, baseline CI e cobertura; fechar lacunas críticas da auditoria antes de ampliar autonomia.
2. P1: contratos de evento/responsabilidade/autorização e persistência, testes de transição e migração. Integrar scheduler/daemon em modo sombra antes de habilitar execução.
3. P2: proatividade, prioridades, briefing e acompanhamento de responsabilidades; integrar secretario e orquestrador, com deduplicação e gates.
4. P3: roteamento, quota e orçamento; provider NanoGPT opt-in, OpenRouter existente, benchmark e DLP; testes fake e chamadas reais autorizadas.
5. P4: memória longitudinal, proveniência, Obsidian e avaliação de Graphify.
6. P5: automações nativas e recuperação de efeitos; adaptadores opcionais n8n.
7. P6: perfis de domínio, comunicação e multimodalidade; cenários completos com integrações reais autorizadas.
8. P7: aprendizado adaptativo e operação contínua; painel com evidências e métricas.
9. P8: hardening, testes reais locais e externos permitidos, matriz multiplataforma, documentação e release.

## Definition of Done por PR
Teste de regressão antes da correção; CI nos SOs suportados; evidência de execução com SHA e ambiente; distinguir mock, integração e campo; documentação/SPEC atualizadas no mesmo commit de comportamento; nenhum segredo em logs; rollback testado para migração; sem ampliar autoridade implícita. Testes reais de APIs dependem de credenciais configuradas pelo operador e orçamento autorizado. Meta de cobertura não substitui cenários de aceitação. Release só após gates e revisão do operador.

## Decisões abertas
SQLite é recomendação sujeita a inventário de persistência e concorrência; não impor migração antecipada. Definir hardware dedicado somente se desejado. Validar preço/franquia NanoGPT e APIs de uso antes de implementação. Nome/versão da release definidos após escopo e aceitação.
