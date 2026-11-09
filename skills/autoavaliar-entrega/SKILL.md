---
name: autoavaliar-entrega
description: Ritual de checagem ANTES de entregar — autoavaliar, autoavaliação, conferir antes de entregar, verificar entrega, está dentro do pedido, revisar minha resposta, checagem final, qualidade da entrega, confiar na resposta, tem certeza. Use ao FINAL de qualquer tarefa com ferramentas, antes de responder ao operador.
nivel: leve
---

# Autoavaliar a entrega (o ritual final)

## Regra inviolável
Nenhuma resposta baseada em ferramentas é entregue sem passar pelas
duas conferências — verificar os FATOS e avaliar contra o PEDIDO.

## O ritual (nesta ordem)
1. **Fatos**: chame `verificar_resposta` com a resposta que você
   preparou e as saídas das ferramentas em `dados_tools`.
   - ✗ (sem lastro) → CORRIJA a afirmação e refaça o passo 1.
   - ~ (incerta) → DECLARE a incerteza na resposta final.
2. **Pedido**: chame `autoavaliar` com o pedido ORIGINAL do operador
   e a sua entrega (critérios vêm do próprio pedido).
   - veredicto CORRIGIR → corrija o que violou e repita.
   - REVISAR → entregue declarando as ressalvas.
3. **Registro**: `tarefa_checkpoint` com `nota=<o que entregou>`; se a
   tarefa acabou, `acao=fechar` (grava no diário).
4. **Entrega**: resposta + rodapé de confiança que as tools devolveram.

## Exemplo
Resposta preparada: "suíte com 241 testes" + dados: "246 OK"
→ verificar_resposta marca ✗ (241 sem lastro) → você corrige para
"246 testes" → autoavaliar dá ENTREGAR → entrega com o rodapé.

## Erro clássico a evitar
Entregar "porque já fiz muito". O ritual custa segundos e é o que
separa resposta de alucinação — ainda mais quando a ação seguinte é
destrutiva (aí `perguntar_operador` é obrigatório).
