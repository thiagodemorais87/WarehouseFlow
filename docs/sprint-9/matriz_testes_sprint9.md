# Matriz de testes — Sprint 9

**Projeto:** WarehouseFlow — Grupo 26  
**Execução:** 06/11/2026  
**Escopo:** funcionalidades e exemplos descritos em [docs/cronograma.md](../cronograma.md), seção Sprint 09.

## Ambiente

- Frontend Jinja e API FastAPI executados no navegador em `http://127.0.0.1:8000`.
- Banco da execução manual: SQLite descartável em `%TEMP%`, com conta e registros temporários de QA.
- Suíte automatizada: Python 3.13.15, SQLite em memória.
- Docker CLI disponível, mas sem daemon; PostgreSQL local indisponível em `localhost:5433`.
- Não foram utilizados nem alterados dados ou volumes persistentes do projeto.

## Cenários funcionais, UI e API

| ID | Cenário | Passos executados | Resultado esperado | Resultado obtido | Status | Evidência / observações |
|---|---|---|---|---|---|---|
| S9-T01 | Health e carregamento do frontend | Consultar `/health` e abrir `/login`. | Health 200 e formulário de login disponível. | Health `200`, versão `dev`; login `200`, formulário renderizado. | PASSOU | [Screenshot](./evidencias/S9-T01-health-e-login.png); log em [api-log.txt](./evidencias/api-log.txt). |
| S9-T02 | E-mail inválido no login | Enviar `qa.sprint9@local.test` pelo formulário. | Rejeitar e não autenticar. | API `400`; UI exibiu “Erro de validação nos dados enviados.” | PASSOU | [Screenshot](./evidencias/S9-T02-email-invalido.png). |
| S9-T03 | Senha inválida | Enviar conta QA com senha incorreta. | `401` e mensagem de credenciais inválidas. | API `401`; UI exibiu “E-mail ou senha incorretos”. | PASSOU | [Screenshot](./evidencias/S9-T03-login-credenciais-invalidas.png). |
| S9-T04 | Login válido e redirecionamento | Autenticar a conta QA temporária. | `200`, redirecionamento ao dashboard e sessão reconhecida. | API `200`, URL `/dashboard`; nome QA e indicadores apareceram. | PASSOU | [Screenshot](./evidencias/S9-T04-login-sucesso-dashboard.png). |
| S9-T05 | Campos obrigatórios de produto | Abrir “Novo produto” e tentar salvar SKU/nome vazios. | Impedir envio sem os campos obrigatórios. | Navegador marcou ambos como obrigatórios; modal permaneceu aberto e não houve cadastro. | PASSOU | [Screenshot](./evidencias/S9-T05-produto-campos-obrigatorios.png). |
| S9-T06 | Peso negativo | Informar peso `-1` no formulário de produto. | Rejeitar valor abaixo do mínimo `0`. | `rangeUnderflow=true`; formulário não foi enviado. | PASSOU | [Screenshot](./evidencias/S9-T06-peso-negativo.png). |
| S9-T07 | Cadastro de produto | Cadastrar produto de QA com SKU único e valores válidos. | API `201` e produto visível na listagem. | API `201`; SKU e dados retornados apareceram na tabela. | PASSOU | [Screenshot](./evidencias/S9-T07-produto-criado.png). |
| S9-T08 | SKU duplicado | Tentar cadastrar novamente o mesmo SKU. | Rejeitar duplicidade com mensagem clara. | API `400`; UI exibiu “Já existe um produto cadastrado com este SKU.” | PASSOU | [Screenshot](./evidencias/S9-T08-sku-duplicado.png). |
| S9-T09 | Edição e persistência de produto | Alterar nome, salvar e recarregar a página. | API `200` e valor atualizado persistido. | API `200`; nome atualizado permaneceu após reload. | PASSOU | [Screenshot](./evidencias/S9-T09-produto-atualizado-persistido.png). |
| S9-T10 | Quantidade zero em pedido | Na criação de pedido, informar quantidade `0`. | Impedir quantidade menor que `1`. | Navegador marcou `rangeUnderflow=true`; modal permaneceu aberto e o pedido não foi enviado. | PASSOU | [Screenshot](./evidencias/S9-T10-quantidade-zero-pedido.png). |
| S9-T11 | Criação de pedido OUTBOUND | Criar pedido de saída com produto e quantidade `3`. | API `201`; pedido e item exibidos. | API `201`; pedido `OUTBOUND`, quantidade `3`, linha visível na tabela. | PASSOU | [Screenshot](./evidencias/S9-T11-pedido-outbound-criado.png). |
| S9-T12 | Filtro de pedidos e navegação lateral | Abrir Pedidos pela navegação; filtrar OUTBOUND e depois INBOUND. | Exibir somente os pedidos compatíveis com o filtro. | OUTBOUND retornou 1 linha; INBOUND retornou 0. | PASSOU | [Screenshot](./evidencias/S9-T12-filtro-pedidos-expedicao.png). |
| S9-T13 | Criação de tarefa de picking | Criar tarefa PICKING vinculada ao pedido de saída. | API `201`; tarefa vinculada e listada. | API `201`; tarefa PICKING ligada ao pedido `1`, visível na tabela. | PASSOU | [Screenshot](./evidencias/S9-T13-tarefa-picking-criada.png). |
| S9-T14 | Otimização por pedido | Selecionar o pedido OUTBOUND e executar otimização. | API `200`, rota e métricas exibidas. | API `200`; rota `START → QA-A-01`, distância final `1`; UI informou sucesso. | PASSOU | [Screenshot](./evidencias/S9-T14-otimizacao-por-pedido.png). |
| S9-T15 | Persistência do histórico de picking | Abrir `/relatorios/picking` após otimizar. | Exibir a execução, rota e resumo persistidos. | Um registro foi exibido, incluindo a rota `START → QA-A-01`. | PASSOU | [Screenshot](./evidencias/S9-T15-relatorio-historico-picking.png). |
| S9-T16 | Relatório de pedidos | Abrir a aba “Relatório de pedidos”. | Exibir os totais do pedido e sua tarefa relacionada. | Relatório mostrou 1 pedido, 1 item, 3 unidades e 1 tarefa. | PASSOU | [Screenshot](./evidencias/S9-T16-navegacao-relatorio-pedidos.png). |
| S9-T17 | Logout e proteção de página | Sair e tentar abrir `/dashboard` novamente. | Remover token e redirecionar ao login. | Token local removido; acesso protegido voltou para `/login`. | PASSOU | [Screenshot](./evidencias/S9-T17-logout-e-redirecionamento.png). |
| S9-T18 | Exclusão de produto com dependências | Tentar excluir produto vinculado a item de pedido/estoque; repetir após correção. | Rejeitar com conflito explícito, preservando o produto. | Antes: API `500` e mensagem genérica. Depois: API `409`, mensagem detalhada e produto mantido. Regressão automatizada passou após correção. | PASSOU após correção | Antes: [screenshot](./evidencias/S9-T18-exclusao-com-dependencias-falha.png), [log da regressão](./evidencias/S9-T18-regressao-antes-correcao.txt). Depois: [screenshot](./evidencias/S9-T18-exclusao-dependencia-409.png), [log](./evidencias/S9-T18-regressao-apos-correcao.txt). |
| S9-T19 | Exclusão de produto sem dependências | Remover referências temporárias e excluir o produto pela UI. | API `204` e produto removido da lista. | API `204`; tabela ficou sem o produto. | PASSOU | [Screenshot](./evidencias/S9-T19-produto-exclusao-sem-vinculos.png). |
| S9-T20 | Autorização e validações da API | Consultar produtos sem token; enviar pedido com quantidade `0`; enviar rota com IDs duplicados. | `401` sem autenticação e `400` para os dois dados inválidos. | Respostas observadas: `401`, `400` e `400`, com detalhes de validação/duplicidade. | PASSOU | [Respostas observadas](./evidencias/S9-T20-api-validation.txt); requisições no [api-log.txt](./evidencias/api-log.txt). |

## Suíte automatizada

| ID | Execução | Resultado | Status | Evidência / observações |
|---|---|---|---|---|
| S9-AUT-01 | `pytest -q --junitxml docs/sprint-9/evidencias/pytest-junit.xml` | 92 passaram, 0 falharam, 1 ignorado; 1 aviso de depreciação do `starlette.testclient` com `httpx`. | PASSOU | [Saída](./evidencias/pytest-results.txt) e [JUnit XML](./evidencias/pytest-junit.xml). |
| S9-AUT-02 | Geração opt-in da matriz (`GERAR_MATRIZ=1`) | Não executada: o teste escreve em `docs/matriz-permissoes.md`, arquivo existente preservado nesta execução. | BLOQUEADO | O teste correspondente foi ignorado pela condição documentada no próprio teste. |
| S9-ENV-01 | Compose com PostgreSQL e Nginx | Não foi possível iniciar: Docker Desktop/Linux daemon indisponível; PostgreSQL também não respondeu em `localhost:5433`. | BLOQUEADO | Foi executada a aplicação com FastAPI + SQLite temporário; integração real com PostgreSQL/Compose continua pendente. |

**Contagem final:** 112 aprovações (20 cenários manuais/UI/API + 92 testes automatizados), 0 falhas após a correção e 2 bloqueios/itens não executados. A falha anterior de S9-T18 está registrada como defeito corrigido, não foi omitida.
