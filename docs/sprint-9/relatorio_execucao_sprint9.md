# Relatório de execução — Sprint 9

**Projeto:** WarehouseFlow — Grupo 26  
**Data:** 06/11/2026  
**Escopo avaliado:** testes completos, correções, validações, navegação e documentação, conforme [cronograma oficial](../cronograma.md).

## Resumo executivo

- **Cenários manuais/UI/API:** 20 passaram após a correção.
- **Pytest:** 92 passaram, 0 falharam, 1 foi ignorado.
- **Falhas finais:** 0.
- **Bloqueios/itens não executados:** 2 — integração Docker/PostgreSQL/Nginx e geração opt-in da matriz de permissões.
- **Bugs encontrados:** 1.
- **Bugs corrigidos:** 1.

Os detalhes de cada cenário, passos, resultados e evidências estão em [matriz_testes_sprint9.md](./matriz_testes_sprint9.md). A falha antes da correção está registrada nos artefatos S9-T18; ela não foi removida dos resultados.

## Funcionalidades testadas

- Login válido, e-mail inválido, credenciais inválidas, logout e proteção de páginas.
- CRUD de produtos, campos obrigatórios, limite de peso, SKU duplicado, atualização e persistência após reload.
- Criação e filtragem de pedidos, quantidade inválida, criação de tarefa PICKING.
- Integração pedido → tarefa → otimização por pedido; rota, métricas e histórico de picking.
- Relatórios de pedidos e picking, incluindo os totais do pedido e a tarefa relacionada.
- Autorização da API e respostas para payload sem autenticação, quantidade inválida e IDs duplicados.
- Exclusão de produto com e sem registros vinculados.

## Execução e ambiente

1. O projeto foi lido e o escopo foi identificado no cronograma como **Sprint 09 — Testes completos**.
2. Docker CLI estava instalado, mas o daemon Linux não estava disponível (`docker info` falhou ao conectar ao pipe do Docker Desktop). Não havia PostgreSQL local escutando em `localhost:5433`.
3. Foi preparado um ambiente Python 3.13.15 isolado em `%TEMP%`, com as dependências já declaradas em `requirements.txt`; nenhum manifesto foi alterado.
4. A API e o frontend Jinja foram iniciados em `http://127.0.0.1:8000`; `/health` respondeu `{"status":"ok","version":"dev"}` e o navegador carregou a UI.
5. Para não tocar no PostgreSQL ou em volumes persistentes, a aplicação manual usou uma base SQLite descartável em `%TEMP%`, com conta e dados temporários de QA. Os fluxos de UI foram exercitados no navegador; chamadas autenticadas verificaram a integração com a API.
6. A suíte automatizada foi executada contra SQLite em memória. O resultado completo ficou salvo em `evidencias/pytest-results.txt` e `evidencias/pytest-junit.xml`.

O SQLite temporário permitiu verificar fluxos funcionais e persistência local, mas não substitui a validação de compatibilidade com PostgreSQL nem o proxy Nginx do Compose.

## Resultado e correção

Foi encontrado um defeito no DELETE de produto com itens vinculados: a API retornava `500` e a interface exibia apenas uma mensagem genérica. A rota agora verifica referências em estoque e itens de pedidos antes da exclusão e responde `409 Conflict`, sem remover o produto. A regressão falhou antes da alteração e passou depois; a UI confirmou tanto o conflito explícito quanto a exclusão `204` quando não há dependências.

Os demais fluxos executados passaram. A suíte emitiu um aviso de depreciação: `httpx` com `starlette.testclient`; não causou falhas. Um teste foi ignorado pelo próprio `skipif`, pois a geração opt-in atualiza `docs/matriz-permissoes.md`, documento existente que foi preservado.

## Evidências

As capturas de tela dos fluxos visuais estão em [evidencias/](./evidencias/), nomeadas por ID de cenário. A pasta também contém:

- log de execução do servidor (`api-log.txt`);
- saída textual e relatório JUnit do Pytest;
- registros da regressão S9-T18 antes e depois da correção;
- respostas observadas nos testes negativos da API.

Nenhum resultado ou screenshot foi criado sem execução correspondente.

## Dificuldades e testes pendentes

- **Docker/PostgreSQL/Nginx:** bloqueados pela indisponibilidade do daemon Docker e do PostgreSQL local. Pendente repetir `docker compose up --build` com Docker Desktop ativo, validar UI em `:8080`, API em `:8000` e persistência no PostgreSQL em `:5433`.
- **Matriz de permissões:** a geração opt-in `GERAR_MATRIZ=1` não foi executada para preservar `docs/matriz-permissoes.md`; os testes de autorização/RBAC presentes na suíte foram executados normalmente.
- Não houve alteração de dados persistentes. A execução real com PostgreSQL permanece pendente.

## Arquivos alterados nesta entrega

- `backend/app/routers/products.py` — conflito explícito ao excluir produto referenciado.
- `tests/test_auth.py` — teste de regressão para exclusão com estoque e item de pedido vinculados.
- `docs/sprint-9/` — matriz, relatório, bugs e evidências desta execução.
