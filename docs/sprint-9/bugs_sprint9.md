# Bugs — Sprint 9

## BUG-S9-01 — Exclusão de produto vinculado provocava erro interno

- **Severidade:** média.
- **Status:** corrigido e retestado.
- **Área:** `DELETE /products/{product_id}` e tela Produtos.
- **Reprodução:** cadastrar produto, associá-lo a estoque e a um item de pedido e tentar excluí-lo pela interface.
- **Resultado antes da correção:** `500 Internal Server Error`; a UI apresentava “Não foi possível excluir o produto.”. A regressão automatizada falhou com `IntegrityError` (`NOT NULL constraint failed: order_items.product_id`).
- **Resultado esperado:** impedir a exclusão enquanto existirem referências e informar o conflito, preservando o produto e os dados relacionados.
- **Causa:** a rota tentava excluir o produto sem verificar registros em `stock` e `order_items`; o ORM tentava limpar a referência não anulável do item de pedido e a falha não era convertida em uma resposta funcional.
- **Correção:** verificar registros dependentes antes do `DELETE` e responder `409 Conflict`, indicando se há registros de estoque e/ou itens de pedidos vinculados.
- **Reteste:** a regressão passou; a interface mostrou `409` com a mensagem explícita e manteve o produto. Após remover as referências temporárias da base SQLite descartável, a exclusão retornou `204` e o produto deixou de aparecer na listagem.
- **Evidências:** [falha anterior na UI](./evidencias/S9-T18-exclusao-com-dependencias-falha.png), [log da regressão antes](./evidencias/S9-T18-regressao-antes-correcao.txt), [UI após correção](./evidencias/S9-T18-exclusao-dependencia-409.png), [regressão após](./evidencias/S9-T18-regressao-apos-correcao.txt), [exclusão sem vínculo](./evidencias/S9-T19-produto-exclusao-sem-vinculos.png).

## Outros defeitos

Não foram confirmados outros defeitos nos cenários executados. A integração com PostgreSQL/Compose não foi validada porque o daemon Docker e o PostgreSQL local estavam indisponíveis; isso é uma limitação de execução, não uma aprovação dessa integração.
