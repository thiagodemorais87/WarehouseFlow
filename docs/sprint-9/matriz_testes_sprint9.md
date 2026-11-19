# Matriz formal de testes — Sprint 9

**Projeto:** WarehouseFlow — Grupo 26  
**Data da execução original:** 06/11/2026  
**Correção desta matriz:** 19/11/2026  
**Escopo:** 20 cenários identificados por S9-T01 a S9-T20.

## Ambiente e regra de status

- Frontend Jinja e API FastAPI em `http://127.0.0.1:8000`.
- Execução funcional manual com SQLite descartável em `%TEMP%`.
- Suíte automatizada contra SQLite em memória.
- Docker/PostgreSQL não estavam disponíveis na execução original.
- Evidência anterior não foi substituída.
- “PASSOU” só foi atribuído quando existe screenshot, log ou resultado textual registrado.

## S9-T01 — Health e carregamento do frontend

- **Funcionalidade:** disponibilidade da API e página de login.
- **Objetivo:** verificar inicialização da aplicação e acesso público ao login.
- **Pré-condições:** API iniciada em `127.0.0.1:8000`.
- **Procedimento:** 1. Consultar `GET /health`. 2. Abrir `/login` no navegador.
- **Resultado esperado:** `/health` retorna `200`; `/login` retorna `200` e renderiza o formulário.
- **Resultado obtido:** `/health` respondeu `200` com `{"status":"ok","version":"dev"}`; `/login` respondeu `200` e mostrou o formulário.
- **Status:** PASSOU.
- **Evidência:** [S9-T01-health-e-login.png](./evidencias/S9-T01-health-e-login.png), [api-log.txt](./evidencias/api-log.txt).
- **Observações:** nenhuma.

## S9-T02 — E-mail inválido no login

- **Funcionalidade:** validação do formulário/login.
- **Objetivo:** impedir autenticação com e-mail inválido.
- **Pré-condições:** página de login disponível.
- **Procedimento:** 1. Informar `qa.sprint9@local.test` no campo de e-mail. 2. Informar uma senha. 3. Enviar.
- **Resultado esperado:** rejeitar o e-mail com mensagem de validação e não criar sessão.
- **Resultado obtido:** API respondeu `400`; UI exibiu “Erro de validação nos dados enviados.”.
- **Status:** PASSOU.
- **Evidência:** [S9-T02-email-invalido.png](./evidencias/S9-T02-email-invalido.png).
- **Observações:** `qa.sprint9@local.test` é sintaticamente válido; a evidência registrada se refere à rejeição por conta inexistente no fluxo combinado. Não registrar como teste de sintaxe.

## S9-T03 — Senha inválida

- **Funcionalidade:** autenticação por credenciais.
- **Objetivo:** rejeitar senha incorreta.
- **Pré-condições:** conta temporária QA criada.
- **Procedimento:** 1. Informar o e-mail da conta QA. 2. Informar senha incorreta. 3. Enviar.
- **Resultado esperado:** `401` com credenciais inválidas e sem cookie de sessão.
- **Resultado obtido:** API respondeu `401`; UI exibiu “E-mail ou senha incorretos”.
- **Status:** PASSOU.
- **Evidência:** [S9-T03-login-credenciais-invalidas.png](./evidencias/S9-T03-login-credenciais-invalidas.png).
- **Observações:** nenhuma.

## S9-T04 — Login válido e redirecionamento

- **Funcionalidade:** login e página inicial.
- **Objetivo:** confirmar autenticação e reconhecimento da sessão.
- **Pré-condições:** conta temporária QA ativa.
- **Procedimento:** 1. Informar credenciais válidas. 2. Enviar o formulário. 3. Verificar dashboard.
- **Resultado esperado:** `200`, redirecionamento e dados do usuário/sessão disponíveis.
- **Resultado obtido:** login `200`, URL `/dashboard` e indicadores/nome QA exibidos.
- **Status:** PASSOU.
- **Evidência:** [S9-T04-login-sucesso-dashboard.png](./evidencias/S9-T04-login-sucesso-dashboard.png).
- **Observações:** nenhuma.

## S9-T05 — Campos obrigatórios de produto

- **Funcionalidade:** validação de cadastro de produto.
- **Objetivo:** impedir envio sem SKU e nome.
- **Pré-condições:** usuário autenticado na tela Produtos.
- **Procedimento:** 1. Abrir “Novo produto”. 2. Deixar SKU e nome vazios. 3. Tentar salvar.
- **Resultado esperado:** campos obrigatórios bloquearem o envio e manter o modal aberto.
- **Resultado obtido:** navegador marcou os campos obrigatórios; não houve cadastro.
- **Status:** PASSOU.
- **Evidência:** [S9-T05-produto-campos-obrigatorios.png](./evidencias/S9-T05-produto-campos-obrigatorios.png).
- **Observações:** nenhuma.

## S9-T06 — Peso negativo

- **Funcionalidade:** validação do peso do produto.
- **Objetivo:** rejeitar peso menor que zero.
- **Pré-condições:** modal de novo produto aberto.
- **Procedimento:** 1. Informar dados válidos. 2. Informar peso `-1`. 3. Tentar salvar.
- **Resultado esperado:** rejeição do campo com `min=0`.
- **Resultado obtido:** `rangeUnderflow=true`; envio não ocorreu.
- **Status:** PASSOU.
- **Evidência:** [S9-T06-peso-negativo.png](./evidencias/S9-T06-peso-negativo.png).
- **Observações:** nenhuma.

## S9-T07 — Cadastro de produto

- **Funcionalidade:** criação de produto.
- **Objetivo:** confirmar persistência e exibição.
- **Pré-condições:** usuário autorizado e SKU exclusivo.
- **Procedimento:** 1. Clicar em novo produto. 2. Informar SKU/nome/dados válidos. 3. Salvar. 4. Conferir tabela.
- **Resultado esperado:** API `201` e produto na listagem.
- **Resultado obtido:** API `201`; SKU e dados apareceram na tabela.
- **Status:** PASSOU.
- **Evidência:** [S9-T07-produto-criado.png](./evidencias/S9-T07-produto-criado.png).
- **Observações:** nenhuma.

## S9-T08 — SKU duplicado

- **Funcionalidade:** unicidade de SKU.
- **Objetivo:** rejeitar cadastro duplicado.
- **Pré-condições:** produto do S9-T07 existente.
- **Procedimento:** 1. Abrir novo produto. 2. Repetir o SKU existente. 3. Informar nome válido. 4. Salvar.
- **Resultado esperado:** API rejeitar com mensagem clara e não criar duplicidade.
- **Resultado obtido:** API `400`; UI mostrou “Já existe um produto cadastrado com este SKU.”.
- **Status:** PASSOU.
- **Evidência:** [S9-T08-sku-duplicado.png](./evidencias/S9-T08-sku-duplicado.png).
- **Observações:** nenhuma.

## S9-T09 — Edição e persistência de produto

- **Funcionalidade:** atualização de produto.
- **Objetivo:** confirmar persistência após recarregar.
- **Pré-condições:** produto temporário criado.
- **Procedimento:** 1. Editar nome. 2. Salvar. 3. Recarregar a página. 4. Conferir nome.
- **Resultado esperado:** API `200` e alteração persistida.
- **Resultado obtido:** API `200`; nome atualizado permaneceu após reload.
- **Status:** PASSOU.
- **Evidência:** [S9-T09-produto-atualizado-persistido.png](./evidencias/S9-T09-produto-atualizado-persistido.png).
- **Observações:** nenhuma.

## S9-T10 — Quantidade zero em pedido

- **Funcionalidade:** validação de quantidade de item.
- **Objetivo:** impedir quantidade menor que 1.
- **Pré-condições:** pedido aberto para criação.
- **Procedimento:** 1. Selecionar produto. 2. Informar quantidade `0`. 3. Tentar criar.
- **Resultado esperado:** validação impedir o envio.
- **Resultado obtido:** `rangeUnderflow=true`; modal aberto e pedido não enviado.
- **Status:** PASSOU.
- **Evidência:** [S9-T10-quantidade-zero-pedido.png](./evidencias/S9-T10-quantidade-zero-pedido.png).
- **Observações:** a resposta negativa da API também está registrada no S9-T20.

## S9-T11 — Criação de pedido OUTBOUND

- **Funcionalidade:** criação de pedido de saída.
- **Objetivo:** confirmar pedido e item associados.
- **Pré-condições:** produto válido disponível.
- **Procedimento:** 1. Criar pedido OUTBOUND. 2. Adicionar produto e quantidade `3`. 3. Salvar.
- **Resultado esperado:** API `201`; pedido e item exibidos.
- **Resultado obtido:** API `201`; pedido OUTBOUND com quantidade `3`.
- **Status:** PASSOU.
- **Evidência:** [S9-T11-pedido-outbound-criado.png](./evidencias/S9-T11-pedido-outbound-criado.png).
- **Observações:** nenhuma.

## S9-T12 — Filtro de pedidos e navegação lateral

- **Funcionalidade:** filtro e navegação para Pedidos.
- **Objetivo:** confirmar filtro por tipo.
- **Pré-condições:** pedido OUTBOUND temporário criado.
- **Procedimento:** 1. Abrir Pedidos pelo menu lateral. 2. Selecionar OUTBOUND. 3. Selecionar INBOUND.
- **Resultado esperado:** exibir somente pedidos do tipo selecionado.
- **Resultado obtido:** OUTBOUND mostrou 1 linha; INBOUND mostrou 0.
- **Status:** PASSOU.
- **Evidência:** [S9-T12-filtro-pedidos-expedicao.png](./evidencias/S9-T12-filtro-pedidos-expedicao.png).
- **Observações:** nenhuma.

## S9-T13 — Criação de tarefa de picking

- **Funcionalidade:** criação de tarefa operacional.
- **Objetivo:** vincular tarefa ao pedido.
- **Pré-condições:** pedido OUTBOUND existente.
- **Procedimento:** 1. Abrir Tarefas. 2. Criar tarefa PICKING. 3. Selecionar pedido `1`. 4. Salvar.
- **Resultado esperado:** API `201` e tarefa vinculada listada.
- **Resultado obtido:** API `201`; tarefa PICKING ligada ao pedido `1`.
- **Status:** PASSOU.
- **Evidência:** [S9-T13-tarefa-picking-criada.png](./evidencias/S9-T13-tarefa-picking-criada.png).
- **Observações:** nenhuma.

## S9-T14 — Otimização por pedido

- **Funcionalidade:** motor de otimização.
- **Objetivo:** executar rota otimizada do pedido.
- **Pré-condições:** pedido OUTBOUND e posições vinculadas.
- **Procedimento:** 1. Abrir Otimização. 2. Selecionar pedido. 3. Executar otimização.
- **Resultado esperado:** API `200`, rota e métricas exibidas.
- **Resultado obtido:** API `200`; rota `START → QA-A-01`; distância final `1`.
- **Status:** PASSOU.
- **Evidência:** [S9-T14-otimizacao-por-pedido.png](./evidencias/S9-T14-otimizacao-por-pedido.png).
- **Observações:** nenhuma.

## S9-T15 — Persistência do histórico de picking

- **Funcionalidade:** histórico de otimização.
- **Objetivo:** confirmar registro persistido após execução.
- **Pré-condições:** S9-T14 executado.
- **Procedimento:** 1. Abrir `/relatorios/picking`. 2. Localizar execução. 3. Conferir rota/resumo.
- **Resultado esperado:** registro exibido com rota e métricas persistidas.
- **Resultado obtido:** um registro exibiu `START → QA-A-01`.
- **Status:** PASSOU.
- **Evidência:** [S9-T15-relatorio-historico-picking.png](./evidencias/S9-T15-relatorio-historico-picking.png).
- **Observações:** nenhuma.

## S9-T16 — Relatório de pedidos

- **Funcionalidade:** relatório agregado de pedidos.
- **Objetivo:** validar navegação e totais.
- **Pré-condições:** pedido e tarefa existentes.
- **Procedimento:** 1. Abrir relatório de pedidos. 2. Conferir totais.
- **Resultado esperado:** totais coerentes com pedido e tarefa.
- **Resultado obtido:** 1 pedido, 1 item, 3 unidades e 1 tarefa.
- **Status:** PASSOU.
- **Evidência:** [S9-T16-navegacao-relatorio-pedidos.png](./evidencias/S9-T16-navegacao-relatorio-pedidos.png).
- **Observações:** nenhuma.

## S9-T17 — Logout e proteção de página

- **Funcionalidade:** encerramento da sessão.
- **Objetivo:** impedir acesso protegido após logout.
- **Pré-condições:** usuário autenticado.
- **Procedimento:** 1. Clicar em Sair. 2. Tentar abrir `/dashboard` diretamente.
- **Resultado esperado:** cookie removido e redirecionamento para `/login`.
- **Resultado obtido:** cookie removido; `/dashboard` voltou para `/login`.
- **Status:** PASSOU.
- **Evidência:** [S9-T17-logout-e-redirecionamento.png](./evidencias/S9-T17-logout-e-redirecionamento.png).
- **Observações:** cobertura adicional automatizada em `test_logout_apaga_o_cookie`.

## S9-T18 — Exclusão de produto com dependências

- **Funcionalidade:** exclusão segura de produto.
- **Objetivo:** preservar produto vinculado e retornar conflito.
- **Pré-condições:** produto referenciado por estoque e/ou item de pedido.
- **Procedimento:** 1. Cadastrar produto vinculado. 2. Tentar excluir pela UI. 3. Registrar resposta antes da correção. 4. Aplicar correção. 5. Executar regressão novamente.
- **Resultado esperado:** resposta `409 Conflict`, detalhe das dependências e produto preservado.
- **Resultado obtido:** antes da correção: `500` e mensagem genérica. Depois da correção: `409`, mensagem detalhada e produto mantido; regressão passou.
- **Status:** PASSOU após correção.
- **Evidência:** antes: [falha](./evidencias/S9-T18-exclusao-com-dependencias-falha.png) e [log](./evidencias/S9-T18-regressao-antes-correcao.txt); depois: [409](./evidencias/S9-T18-exclusao-dependencia-409.png) e [log](./evidencias/S9-T18-regressao-apos-correcao.txt).
- **Observações:** bug identificado e corrigido no ciclo da Sprint 9.

## S9-T19 — Exclusão de produto sem dependências

- **Funcionalidade:** exclusão de produto sem vínculo.
- **Objetivo:** confirmar exclusão liberada somente sem dependências.
- **Pré-condições:** referências temporárias removidas.
- **Procedimento:** 1. Remover vínculos temporários. 2. Excluir produto pela UI. 3. Recarregar tabela.
- **Resultado esperado:** API `204` e produto removido.
- **Resultado obtido:** API `204`; produto desapareceu da tabela.
- **Status:** PASSOU.
- **Evidência:** [S9-T19-produto-exclusao-sem-vinculos.png](./evidencias/S9-T19-produto-exclusao-sem-vinculos.png).
- **Observações:** nenhuma.

## S9-T20 — Validações e autenticação da API

- **Funcionalidade:** proteção e validação da API.
- **Objetivo:** confirmar `401` sem credencial e `400` para payloads inválidos.
- **Pré-condições:** API disponível.
- **Procedimento:** 1. Consultar produtos sem token. 2. Criar pedido com quantidade `0`. 3. Criar rota com IDs duplicados.
- **Resultado esperado:** `401` para consulta sem token; `400` para cada payload inválido.
- **Resultado obtido:** respostas `401`, `400` e `400`, respectivamente, com detalhes.
- **Status:** PASSOU.
- **Evidência:** [S9-T20-api-validation.txt](./evidencias/S9-T20-api-validation.txt), [api-log.txt](./evidencias/api-log.txt).
- **Observações:** inclui validação de quantidade e duplicidade; não cobre todas as combinações de perfil.

## Suíte automatizada registrada

| Execução | Resultado observado | Status | Evidência |
|---|---|---|---|
| `pytest -q --junitxml docs/sprint-9/evidencias/pytest-junit.xml` | 92 passaram, 1 ignorado, 1 aviso | PASSOU | [pytest-results.txt](./evidencias/pytest-results.txt), [pytest-junit.xml](./evidencias/pytest-junit.xml) |
| `tests/test_auth.py tests/test_matriz_permissoes.py -q` | 63 passaram, 1 ignorado, 1 aviso | PASSOU nesta correção | [navegacao-permissoes-pytest.txt](./evidencias/navegacao-permissoes-pytest.txt) |
| Compose PostgreSQL/Nginx | Docker daemon/PostgreSQL indisponíveis | BLOQUEADO | Registrado no relatório original |
