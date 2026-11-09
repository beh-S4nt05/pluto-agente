---
name: interrogar
description: Perguntas incisivas que furam o pedido antes de executar (grill) — interrogar, questionar, fazer perguntas difíceis, entrevista de requisitos, apontar furos, blindar o pedido, revisar o pedido antes de aceitar, e se der errado, casos de borda, borda. Use em pedidos importantes/arriscados ANTES de planejar.
nivel: rapido
---

# Interrogar (o revisor chato do pedido)

## Regra inviolável
Pergunta boa tem PORQUÊ e OPÇÃO DE RESPOSTA — não é "me conta mais".

## Método
1. Finja ser o revisor chato: leia o pedido procurando AMBIGUIDADES,
   CASOS DE BORDA e CRITÉRIOS FALTANDO.
2. Gere até 5 perguntas, cada uma com o porquê e, quando possível,
   2 opções de resposta ("A ou B?").
3. Perguntas que bloqueiam → `perguntar_operador`. As demais →
   suposição declarada.
4. Depois das respostas: atualize o PRD/plano com o que mudou.

## O que um revisor chato pergunta
- "Pronto para QUEM — como essa pessoa testa?"
- "E quando [caso de borda] acontecer?" (vazio, offline, dado errado)
- "O que define 'funcionando'? Dá para medir?"
- "O que pode quebrar se eu fizer isso?" (riscos, dados)
- "Isto aqui é DEVE ou MELHOR TER?"

## Exemplo
Pedido: "automatiza o backup"
Pergunta: "Se o disco externo estiver desplugado, o backup falha
alto (aviso) ou silencia e tenta depois? A=falha alto, B=tenta
depois" — porque muda o design do gatilho.

## Erro clássico a evitar
Interrogar pedido trivial ("qual cor do relatório?"). Risco baixo +
pedido claro → executa com eco e suposições.
