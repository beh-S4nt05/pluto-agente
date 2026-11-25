# ADR — Motor nativo opcional Python + Rust

Status: direção aprovada pelo operador; implementação condicionada a benchmarks.
Complementa SPEC-SECRETARIADO-COGNITIVO.md (SEC-05, SEC-11, SEC-12).

## Evidência de inspeção da base 271f172
- knowledge.buscar recarrega JSON e retokeniza todos os blocos a cada consulta; priorizar índice incremental/invertido antes de portar linguagem.
- vault.buscar percorre Markdown até oito resultados; misses percorrem todo o acervo. Preservar ordem, trechos e fonte; investigar Unicode, links simbólicos e limites.
- grafo.build usa AST Python e SQLite já nativos em partes; rglob filtra diretórios após descoberta, rebuild apaga o índice anterior. Medir pruning e publicação atômica.
- grafo.path usa list.pop(0) e copia caminhos; avaliar deque e predecessores antes de Rust. Resolução por nome curto é heurística, não prova semântica.
- MemoryStore e demais validadores: inventariar formatos e contratos antes de migrar. Integridade estrutural não comprova verdade factual.

## Decisão
Python mantém políticas, autorização, orquestração, fontes de verdade, LLMs e auditoria.
Rust opcional via PyO3/Maturin, sem serviço adicional, para operações CPU-bound comprovadas. Priorizar funções puras em lote, sem acesso autônomo ao filesystem ou rede; receber entradas previamente autorizadas. Fallback Python mantém semântica e segurança; falha de autorização nunca vira fallback permissivo. Não migrar hashing já nativo, SQL, AST ou inferência sem evidência.
O índice é derivado; Markdown e estado persistente continuam sob os contratos existentes. Sem duplicação de fontes de verdade. Limitar threads, tamanho de entradas e memória. Preservar Unicode, ordenação, provenance, erros, cancelamento e compatibilidade multiplataforma. Sem unsafe próprio por padrão. Não trocar SHA-256 de atualização por BLAKE3.

## Plano executável
R0: benchmark sintético reproduzível dos caminhos reais de RAG, vault e grafo; medir separadamente indexação e consultas hit/miss; depois testar acervo autorizado local.
R1: otimização algorítmica Python/SQLite, regressões e nova baseline.
R2: protótipo nativo isolado para o hotspot CPU-bound dominante, com paridade de resultados e extensão opcional.
R3: integração por adaptador, testes Python-only e nativo, Linux/macOS/Windows e ARM64 conforme disponibilidade.
R4: ampliar a memória incremental e grafo apenas após evidências; integração com secretariado.
R5: release com wheels verificadas, fallback, rollback e documentação.

## Gate de adoção
Mesma fixture, hardware, versões, condições e SHA; medir mediana e p95, throughput, pico de memória e impacto no startup. Comparar Python otimizado, não só baseline ingênua. Meta proposta: pelo menos 2x no hotspot e ganho end-to-end relevante (>=20% no fluxo alvo) ou redução mensurável de recursos sem regressão de latência. Paridade e segurança são obrigatórias independentemente do ganho. Sem limites de desempenho rígidos em CI compartilhado; publicar resultados e investigar regressões. Não declarar aceleração antes de medir.
