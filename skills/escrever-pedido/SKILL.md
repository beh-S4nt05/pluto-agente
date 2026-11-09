---
name: escrever-pedido
description: Escrever o pedido como documento (PRD curto) — prd, documento de requisitos, especificação, especificar, descrever o pedido por escrito, escopo do projeto, requisito, requisitos, antes de codar, documentar o que foi pedido. Use quando o pedido for vago, grande ou for a base de um projeto.
nivel: leve
---

# Escrever pedido (PRD curto)

## Regra inviolável
PRD curto e verificável — não é monografia. Cada requisito tem que dar
para testar com sim/não depois de pronto.

## Estrutura (máx. 1 tela)
1. **Contexto**: 2 linhas — por que isto existe.
2. **Objetivo**: 1 frase — o que fica pronto no final.
3. **Requisitos**: lista com DEVE (obrigatório) / MELHOR TER (bônus) /
   NÃO FAZER (fora de escopo explícito).
4. **Critérios de aceite**: o checklist que prova que está pronto —
   frases verificáveis ("rodando X, acontece Y").
5. **Riscos/premissas**: só os relevantes.

## Depois de escrever
- Grave no checkpoint da tarefa: `tarefa_checkpoint` com
  `objetivo=<objetivo do PRD>` (os critérios de aceite entram como
  critérios automáticos).
- Confirme com o operador ANTES de planejar a execução.

## Exemplo
Requisito: "DEVE mostrar saldo por conta"; critério: "ao abrir a
página, o saldo de cada conta aparece e bate com o livro-caixa".
NÃO FAZER: "importar extrato do banco" (isso é outro pedido).
