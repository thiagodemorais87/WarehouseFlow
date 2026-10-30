# Sprint 8 — Registro de execução e evidências

**Data:** 30/10/2026  
**Ambiente:** aplicação local via Docker Compose; interface `http://127.0.0.1:8080`, API `http://127.0.0.1:8000` e PostgreSQL do projeto.  
**Capturas:** arquivos PNG do viewport da aplicação, em 1920 × 1080, sem recorte ou redimensionamento.  
**Alterações no produto:** nenhuma. Os registros temporários criados nos testes foram removidos.

## Resumo

| Cenário | Resultado |
|---|---|
| 1 — Login e perfis | **APROVADO** — credenciais e permissões da API verificadas; não havia usuário GESTOR previamente cadastrado. |
| 2 — CRUD de produtos | **APROVADO** — criação, consulta, edição e exclusão concluídas; ressalva sobre precisão do volume registrada abaixo. |
| 3 — Otimização de picking | **APROVADO** — rota e métricas verificadas na interface e na API. |
| 4 — Permissão negada | **APROVADO** — OPERADOR recebeu HTTP 403 ao tentar criar produto. |
| 5 — Persistência | **APROVADO** — produto continuou disponível após reiniciar os três serviços. |
| Suíte automatizada | **APROVADO** — 80 testes passaram; 1 aviso de depreciação. |

## Inicialização e validação automatizada

- Iniciados os contêineres existentes com `docker compose start`. A interface e a API responderam HTTP 200.
- Ao final, reiniciados banco, API e interface com `docker compose restart`; a API recuperou o estado saudável e `/health` retornou `{"status":"ok"}`.
- Suíte executada no contêiner Python do projeto, com SQLite em memória isolado: `python -m pytest -q -p no:cacheprovider`.
- **Resultado:** 80 passed, 1 warning em `starlette.testclient` sobre depreciação do uso de `httpx`.

## Cenário 1 — Login e perfis

**Identificação:** C1 — autenticação e autorização por perfil.  
**Objetivo/procedimento:** testar credenciais válidas e inválidas e verificar leitura e escrita de produtos e usuários com ADMIN, GESTOR e OPERADOR.  
**Esperado:** login válido autentica; inválido é recusado; as operações de escrita respeitam o perfil.

**Resultado observado:**

- `GET /login` — HTTP 200.
- `POST /auth/login` com senha inválida — HTTP 401 e mensagem “E-mail ou senha incorretos”.
- `POST /auth/login` com ADMIN — HTTP 200; token emitido e navegação ao dashboard. Indicadores carregados: 4 produtos, 155 unidades, 1 pedido pendente e 0 tarefas em andamento.
- O banco tinha perfis `ADMIN`, `OPERATOR` e `MANAGER`, mas nenhum usuário GESTOR. Foi criado um usuário MANAGER temporário para validar esse perfil; a normalização existente o tratou como GESTOR. A conta temporária foi removida ao final.
- Login e `GET /products/` e `GET /users/` retornaram HTTP 200 para os três perfis.
- `POST /products/`: ADMIN HTTP 201; GESTOR HTTP 201; OPERADOR HTTP 403.
- `POST /users/`: ADMIN HTTP 201; GESTOR HTTP 403; OPERADOR HTTP 403.
- Os produtos e usuários temporários de autorização foram removidos com HTTP 204.

**Status:** APROVADO.  
**Evidências:** [login-1.png](./login-1.png), [login-2.png](./login-2.png), [login-3.png](./login-3.png), [permissao-negada-1.png](./permissao-negada-1.png), [permissao-negada-2.png](./permissao-negada-2.png).

## Cenário 2 — CRUD de produtos

**Identificação:** C2 — CRUD da entidade Produto.  
**Objetivo/procedimento:** pela interface, criar um produto temporário com SKU `S8-20261030-1519`, consultar a lista, alterar seu nome e excluí-lo.  
**Esperado:** respostas de sucesso, dados visíveis após criação/edição e registro ausente após exclusão.

**Resultado observado:**

- `GET /products/` — HTTP 200; lista inicial com 4 produtos. O produto preexistente `111222` foi preservado.
- `POST /products/` — HTTP 201; produto criado com ID 12.
- A atualização da lista (`GET /products/`) exibiu SKU, nome e campos enviados.
- `PUT /products/12` — HTTP 200; nome atualizado e visível na lista.
- `DELETE /products/12` — HTTP 204; produto deixou de aparecer na lista.
- **Ressalva de precisão:** o formulário aceita volume com três casas decimais (`step="0.001"`), mas o valor `0.015` retornou e foi exibido como `0.02`. O dado foi persistido com arredondamento; requer confirmação da precisão esperada.

**Status:** APROVADO, com a ressalva de precisão registrada.  
**Evidências:** [crud-produtos-1.png](./crud-produtos-1.png), [crud-produtos-2.png](./crud-produtos-2.png), [crud-produtos-3.png](./crud-produtos-3.png), [crud-produtos-4.png](./crud-produtos-4.png), [crud-produtos-5.png](./crud-produtos-5.png), [crud-produtos-6.png](./crud-produtos-6.png), [crud-produtos-7.png](./crud-produtos-7.png).

## Cenário 3 — Otimização de picking

**Identificação:** C3 — cálculo de rota e métricas.  
**Objetivo/procedimento:** usar o formulário implementado com início `(0,0)` e quatro posições válidas: FAR1 `(10,0)`, NEAR1 `(1,0)`, FAR2 `(11,0)` e NEAR2 `(2,0)`. Também consultar o endpoint por pedido para o pedido de saída existente `1`.  
**Esperado:** rota válida e métricas coerentes; no conjunto manual, distância otimizada menor que a original.

**Resultado observado:**

- `POST /optimization/route` — HTTP 200.
- Rota original: `START → FAR1 → NEAR1 → FAR2 → NEAR2`.
- Nearest Neighbor e 2-opt: `START → NEAR1 → NEAR2 → FAR1 → FAR2`.
- Distância original: **38**; Nearest Neighbor: **11**; 2-opt/final: **11**; economia: **27**; redução: **71,05%**; **4** localizações; execução observada: aproximadamente **0,030 ms**.
- `POST /optimization/route/by-order` com `order_id=1` — HTTP 200; rota `START → A1-01-A → A1-01-B`, 2 localizações, distância 3 antes e depois. Essa ordem válida não apresentou redução.
- A execução manual calcula e apresenta a rota; não grava automaticamente um histórico de resultados.

**Status:** APROVADO.  
**Evidências:** [otimizacao-picking-1.png](./otimizacao-picking-1.png), [otimizacao-picking-2.png](./otimizacao-picking-2.png), [otimizacao-picking-3.png](./otimizacao-picking-3.png).

## Cenário 4 — Permissão negada

**Identificação:** C4 — tentativa de escrita como OPERADOR.  
**Objetivo/procedimento:** autenticar como OPERADOR, consultar produtos e tentar criar um produto pela interface.  
**Esperado:** leitura permitida e escrita restrita bloqueada.

**Resultado observado:**

- `POST /auth/login` — HTTP 200; token com perfil `OPERATOR`.
- `GET /products/` — HTTP 200; operador consultou a lista.
- `POST /products/` — HTTP 403; a interface exibiu “Acesso negado: seu perfil não possui permissão para esta operação.” Nenhum produto foi criado.
- A verificação complementar do cenário 1 confirmou HTTP 403 em `POST /users/` para GESTOR e OPERADOR.

**Status:** APROVADO.  
**Evidências:** [permissao-negada-1.png](./permissao-negada-1.png), [permissao-negada-2.png](./permissao-negada-2.png).

## Cenário 5 — Persistência de dados

**Identificação:** C5 — produto mantido após reiniciar a aplicação.  
**Objetivo/procedimento:** criar o produto temporário `S8-PERSIST-20261030`, reiniciar banco, API e interface, recarregar a lista e conferir o registro.  
**Esperado:** o registro continuar salvo depois do reinício.

**Resultado observado:**

- `POST /products/` — HTTP 201; produto criado com ID 13.
- `docker compose restart` reiniciou os três serviços; `/health` voltou a responder HTTP 200.
- Após recarregar a interface, `GET /products/` — HTTP 200; o SKU e os dados do produto permaneceram visíveis.
- Para não deixar dados de QA no banco, o produto temporário foi excluído depois da captura — HTTP 204.

**Status:** APROVADO.  
**Evidências:** [persistencia-1.png](./persistencia-1.png), [persistencia-2.png](./persistencia-2.png).

## Funcionalidades não testadas ou limitações de escopo

- **Tela de gestão de usuários:** o item “Usuários” do menu aponta para `#`; não há tela de administração acessível pela interface. As operações implementadas foram verificadas pela API.
- **Histórico persistido de otimizações:** não foi testado como fluxo persistente, pois a interface executa o cálculo e mostra o resultado, mas não salva automaticamente um registro de histórico.
- **Conta GESTOR preexistente:** não havia usuário desse perfil no banco inicial. O perfil foi verificado com uma conta temporária baseada no papel `MANAGER`, removida ao final.
- Não foram alterados nem excluídos produtos preexistentes; somente registros temporários com prefixo `S8-` foram usados e removidos.

## Problemas e observações encontrados

1. **Precisão de volume:** entrada `0.015` foi armazenada como `0.02`, embora o campo aceite incrementos de `0.001`.
2. **Identidade no dashboard:** após autenticação como ADMIN, o cabeçalho continua exibindo o usuário estático “Usuário Teste”; não reflete a identidade autenticada.
3. **Gestão de usuários na interface:** item de navegação sem tela (`href="#"`); o backend de usuários existe e teve suas permissões testadas.
4. **Dados iniciais de perfis:** o banco contém o papel `MANAGER`, mas não uma conta GESTOR pronta para autenticação; foi necessário criar uma conta de teste temporária.

Nenhum dos problemas acima foi corrigido nesta execução; não houve alteração no código da aplicação, README, cronograma ou documentação geral das sprints.
