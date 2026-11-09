---
name: pedido-para-plano
description: Transformar pedido aprovado em plano executável — plano, planejar, planejamento, plano de execução, etapas, passos, quebrar em tarefas, dividir o trabalho, roadmap, como vou fazer, por onde começo, sequência de execução. Use quando o pedido/PRD está claro e falta o COMO.
nivel: leve
---

# Pedido para plano (o COMO antes do fazer)

## Regra inviolável
Plano é sequência de passos que você consegue EXECUTAR e CONFERIR —
não lista de boas intenções.

## Método
1. Liste os passos em ordem, numerados. Cada passo tem: **ação** (o
   quê) + **ferramenta** (com o quê) + **pronto** (como sei que acabou).
2. O 1º passo é pequeno e verificável (desbloqueia o resto).
3. Passos destrutivos ficam marcados com ⚠ (exigem confirmação).
4. Grave no checkpoint: `tarefa_checkpoint` com `plano=<passos>` e
   `proximos=<1º passo>` — o plano sobrevive a restart (P1).
5. Execute UM passo por vez; ao concluir, `nota=<feito>` no checkpoint.

## Exemplo
Pedido: "coloca CI no repo"
Plano: 1) escrever workflow (write_file) — pronto: YAML válido;
2) rodar suíte local (run_command) — pronto: 249/249; 3) commit+push
(run_command) — pronto: push aceito; 4) conferir o run no Actions
(web_fetch) — pronto: verde nos 3 SOs.

## Erro clássico a evitar
Plano de 15 passos vagos ("melhorar o sistema"). Se não dá para dizer
"pronto", não é passo.
