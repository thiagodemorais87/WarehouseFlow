# WarehouseFlow — referência atual da API

Este contrato foi conferido com os routers, schemas Pydantic, dependências de
autorização, serviços e OpenAPI da aplicação. Os exemplos descrevem a forma do
contrato; IDs, datas e valores calculados variam conforme a base.

- **Base local da API:** `http://127.0.0.1:8000`
- **Swagger UI:** [`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs)
- **OpenAPI JSON:** [`http://127.0.0.1:8000/openapi.json`](http://127.0.0.1:8000/openapi.json)
- **Health check:** `GET /health`

O Compose publica a UI/proxy em `http://127.0.0.1:8080` e a API em
`http://127.0.0.1:8000`. O Swagger é servido pela API em `/docs`.

## Convenções de autenticação e erros

As rotas privadas aceitam `Authorization: Bearer <access_token>` ou o cookie
`access_token` emitido no login. `POST /auth/login` devolve o JWT no JSON e
também o grava em cookie `HttpOnly`, `SameSite=Lax`. O token tem validade
configurada de 8 horas.

| HTTP | Formato / significado |
|---|---|
| `400` | Validação de entrada: `{"detail":"Erro de validação nos dados enviados.","errors":["Campo 'quantity': ..."]}`. Regras de integridade do banco também podem retornar `400`. |
| `401` | Sem autenticação, token inválido/expirado, usuário inexistente/inativo, ou credenciais inválidas. |
| `403` | Perfil sem permissão para a operação. |
| `404` | Recurso relacionado ou identificado não encontrado. |
| `409` | Conflito de negócio, referência/duplicidade no banco ou regra que impede a operação. |
| `422` | Não é o código de validação da aplicação: o handler converte erros de entrada em `400`; o OpenAPI foi ajustado para refletir isso. |

O handler de integridade retorna `409` para duplicidade e chave estrangeira e
`400` para outras violações de integridade. Uma resposta HTTP de sucesso não
implica que chamadas a endpoints diferentes tenham sido feitas na mesma
transação.

## Autenticação (`/auth/*`)

### `POST /auth/login`

- **Acesso:** público.
- **Body:** `email` (e-mail válido) e `password` (não vazio).
- **Exemplo:** `{"email":"admin@warehouseflow.com","password":"<senha>"}`
- **Sucesso `200`:** `{"access_token":"<JWT>","token_type":"bearer"}`; também define o cookie HttpOnly.
- **Erros:** `400` body inválido; `401` `"E-mail ou senha incorretos"`; `400` usuário inativo; `403` usuário sem perfil de acesso.

### `GET /auth/me`

- **Acesso:** autenticado; qualquer role.
- **Path/query/body:** nenhum.
- **Exemplo:** `GET /auth/me` com Bearer ou cookie.
- **Sucesso `200`:** `{"id":1,"name":"Carlos Admin","email":"admin@warehouseflow.com","role":"ADMIN","is_active":true}`.
- **Erros:** `401` `"Token inválido ou expirado"`.

### Rotas de sessão da interface

Estas rotas servem HTML/formulários; não substituem os endpoints JSON de
`/auth`.

| Método e caminho | Entrada / sucesso | Erros e acesso |
|---|---|---|
| `GET /login` | Público; HTML `200`. | Não requer autenticação. |
| `POST /login` | Form fields `email`, `password`; login válido redireciona `303` para `/inicio` e define cookie. | `401` para credenciais inválidas; `400` validação do formulário. |
| `GET /inicio` | Cookie válido; HTML `200`. | Sem sessão redireciona `303` para `/login`. |
| `POST /logout` | Limpa `access_token`, retorna redirect `303` para `/login`; sem body. | Não exige role. |

## Pedidos (`/orders`)

Todas as rotas exigem usuário autenticado. `GET` é permitido a qualquer role.
Criação/alteração de pedido e itens permite `ADMIN`, `GESTOR` e `OPERADOR`;
exclusão de pedido exige `ADMIN` ou `GESTOR`.

### `POST /orders/`

- **Entrada:** body `type` (`INBOUND`/`OUTBOUND`), `status` opcional (padrão `PENDING`) e `items` com pelo menos um item; cada `quantity` deve ser maior que zero.
- **Exemplo:** `{"type":"OUTBOUND","status":"PENDING","items":[{"product_id":1,"quantity":2}]}`
- **Sucesso `201`:** `{"id":12,"type":"OUTBOUND","status":"PENDING","created_at":"2026-11-13T10:00:00","items":[{"id":31,"order_id":12,"product_id":1,"quantity":2}]}`
- **Erros:** `400` body/enum/quantidade inválidos; `401` sem sessão; `403` role; `404` produto inexistente; `409` integridade.

### `GET /orders/`

- **Entrada:** query `type`, `status`, `skip` (padrão `0`, mínimo `0`), `limit` (padrão `100`, intervalo `1..500`).
- **Exemplo:** `GET /orders/?type=OUTBOUND&status=PENDING&skip=0&limit=50`
- **Sucesso `200`:** lista de objetos `OrderResponse`, cada um com `id`, `type`, `status`, `created_at` e `items`.
- **Erros:** `400` paginação inválida; `401` sem sessão.
- `type` e `status` são filtros por igualdade; o router não rejeita strings desconhecidas como enum de query.

### `GET /orders/{order_id}`

- **Entrada:** path `order_id` inteiro.
- **Exemplo:** `GET /orders/12`
- **Sucesso `200`:** objeto `OrderResponse` com os itens do pedido.
- **Erros:** `400` path inválido; `401`; `404` `"Pedido não encontrado."`.

### `PUT /orders/{order_id}`

- **Entrada:** path `order_id`; body parcial com `type` e/ou `status`.
- **Exemplo:** `{"status":"PROCESSING"}`
- **Sucesso `200`:** `OrderResponse` atualizado.
- **Erros:** `400` body/enum inválido; `401`; `403`; `404` pedido inexistente; `409` integridade.

### `DELETE /orders/{order_id}`

- **Acesso:** `ADMIN`, `GESTOR`.
- **Entrada:** path `order_id`; sem body.
- **Exemplo:** `DELETE /orders/12`
- **Sucesso `204`:** sem body.
- **Erros:** `400` path inválido; `401`; `403`; `404` `"Pedido não encontrado."`.

### `POST /orders/{order_id}/items`

- **Acesso:** `ADMIN`, `GESTOR`, `OPERADOR`.
- **Entrada:** path `order_id`; body `{"product_id":1,"quantity":3}` (`quantity > 0`).
- **Sucesso `201`:** `{"id":32,"order_id":12,"product_id":1,"quantity":3}`. Se o produto já estiver no pedido, soma a quantidade e devolve o item atualizado.
- **Erros:** `400` body/quantidade inválidos; `401`; `403`; `404` pedido ou produto inexistente; `409` integridade.

### `PUT /orders/{order_id}/items/{item_id}`

- **Acesso:** `ADMIN`, `GESTOR`, `OPERADOR`.
- **Entrada:** paths `order_id`, `item_id`; body `{"quantity":4}` (`quantity > 0`).
- **Sucesso `200`:** `OrderItemResponse` atualizado.
- **Erros:** `400` body/IDs inválidos; `401`; `403`; `404` `"Item não encontrado no pedido informado."`.

### `DELETE /orders/{order_id}/items/{item_id}`

- **Acesso:** `ADMIN`, `GESTOR`, `OPERADOR`.
- **Entrada:** paths `order_id`, `item_id`; sem body.
- **Sucesso `204`:** sem body.
- **Erros:** `400` path inválido; `401`; `403`; `404` item fora do pedido ou inexistente; `409` não permite remover o último item do pedido.

## Tarefas (`/tasks`)

Todas exigem autenticação. Leitura é disponível a qualquer role. Escrita
permite `ADMIN`, `GESTOR` e `OPERADOR`, exceto exclusão, que exige `ADMIN` ou
`GESTOR`. Um `OPERADOR` só lista/consulta/altera tarefas atribuídas a si e não
pode mudar `assigned_user_id`.

### `POST /tasks/`

- **Acesso:** `ADMIN`, `GESTOR`, `OPERADOR`.
- **Entrada:** body `type` (`PICKING`, `PUTAWAY`, `REPLENISHMENT`), `status` opcional (padrão `PENDING`), `order_id`, `assigned_user_id` opcional.
- **Exemplo:** `{"type":"PICKING","status":"PENDING","order_id":12,"assigned_user_id":2}`
- **Sucesso `201`:** `{"id":8,"type":"PICKING","status":"PENDING","order_id":12,"assigned_user_id":2,"created_at":"2026-11-13T10:00:00","optimization_results":[]}`
- **Erros:** `400` body/enum inválidos; `401`; `403`; `404` pedido ou usuário atribuído não encontrado.

### `GET /tasks/`

- **Entrada:** query `type`, `status`, `assigned_user_id`, `order_id`, `skip` (`0`), `limit` (`100`, intervalo `1..500`).
- **Exemplo:** `GET /tasks/?type=PICKING&status=PENDING&order_id=12`
- **Sucesso `200`:** lista de `TaskResponse`.
- **Erros:** `400` query/paginação inválida; `401`.
- Para `OPERADOR`, o filtro por usuário autenticado é aplicado antes dos demais filtros.

### `GET /tasks/{task_id}`

- **Entrada:** path `task_id`.
- **Exemplo:** `GET /tasks/8`
- **Sucesso `200`:** `TaskResponse`.
- **Erros:** `400` path inválido; `401`; `403` operador consultando tarefa de outra pessoa; `404` `"Tarefa não encontrada."`.

### `PUT /tasks/{task_id}`

- **Acesso:** `ADMIN`, `GESTOR`, `OPERADOR`.
- **Entrada:** path `task_id`; body parcial com `type`, `status`, `assigned_user_id`.
- **Exemplo:** `{"status":"IN_PROGRESS"}`
- **Sucesso `200`:** `TaskResponse` atualizado.
- **Erros:** `400` body/enum inválidos; `401`; `403` role/tarefa de outro operador/tentativa de reatribuição por operador; `404` tarefa ou usuário atribuído inexistente.

### `DELETE /tasks/{task_id}`

- **Acesso:** `ADMIN`, `GESTOR`.
- **Entrada:** path `task_id`; sem body.
- **Exemplo:** `DELETE /tasks/8`
- **Sucesso `204`:** sem body.
- **Erros:** `400` path inválido; `401`; `403`; `404` `"Tarefa não encontrada."`.

## Usuários e cargos (`/users`)

Todas exigem autenticação. Consultas de usuários/cargos aceitam qualquer role;
criação, alteração e exclusão exigem `ADMIN`. `UserResponse` não expõe
`password` nem `password_hash`.

### `POST /users/roles/`

- **Acesso:** `ADMIN`.
- **Body:** `{"name":"SUPERVISOR"}` (`name` até 50 caracteres; salvo em maiúsculas).
- **Sucesso `201`:** `{"id":4,"name":"SUPERVISOR"}`.
- **Erros:** `400` nome inválido ou `"Cargo já cadastrado."`; `401`; `403`; `409` integridade.

### `GET /users/roles/`

- **Entrada:** sem parâmetros.
- **Sucesso `200`:** `[{"id":1,"name":"ADMIN"},{"id":2,"name":"OPERADOR"}]`.
- **Erros:** `401`.

### `POST /users/`

- **Acesso:** `ADMIN`.
- **Body:** `name` (até 100), e-mail válido até 100 caracteres, `password` de 6 a 72 caracteres e `role_id` opcional.
- **Exemplo:** `{"name":"Ana Operadora","email":"ana@example.com","password":"Senha-forte-1","role_id":2}`
- **Sucesso `201`:** `UserResponse`, por exemplo `{"id":9,"name":"Ana Operadora","email":"ana@example.com","role_id":2,"is_active":true,"created_at":"2026-11-13T10:00:00","role":{"id":2,"name":"OPERADOR"}}`.
- **Erros:** `400` body/e-mail/senha inválidos ou `"E-mail já está em uso."`; `401`; `403`; `404` `"Role não encontrada."`; `409` integridade.

### `GET /users/`

- **Entrada:** query opcional `role_id`, `role` (`ADMIN`, `GESTOR`, `OPERADOR`), `email` (busca parcial), `skip` (`0`), `limit` (`100`, intervalo `1..500`).
- **Exemplo:** `GET /users/?role=OPERADOR&email=ana&skip=0&limit=20`
- **Sucesso `200`:** lista de `UserResponse` sem senha/hash.
- **Erros:** `400` role/paginação inválida; `401`.
- O filtro aceita os aliases de banco `MANAGER` e `OPERATOR` para `GESTOR` e `OPERADOR`.

### `GET /users/{user_id}`

- **Entrada:** path `user_id`.
- **Exemplo:** `GET /users/9`
- **Sucesso `200`:** `UserResponse`.
- **Erros:** `400` path inválido; `401`; `404` `"Usuário não encontrado."`.

### `PUT /users/{user_id}`

- **Acesso:** `ADMIN`.
- **Entrada:** path `user_id`; body parcial com `name`, `email`, `role_id`, `password`, `is_active`. `password` informado é armazenado como hash.
- **Exemplo:** `{"name":"Ana Operadora (turno B)","is_active":true}`
- **Sucesso `200`:** `UserResponse` atualizado, sem senha/hash.
- **Erros:** `400` body/e-mail inválido ou campos não anuláveis explicitamente nulos; `401`; `403`; `404` usuário inexistente; `409` integridade.

### `DELETE /users/{user_id}`

- **Acesso:** `ADMIN`.
- **Entrada:** path `user_id`; sem body.
- **Exemplo:** `DELETE /users/9`
- **Sucesso `204`:** sem body.
- **Erros:** `400` path inválido; `401`; `403`; `404` `"Usuário não encontrado."`; `409` integridade.

## Relatórios (`/reports`)

`GET /reports/dashboard` permite qualquer usuário autenticado. Os demais
relatórios e exportações exigem `ADMIN` ou `GESTOR`. Filtros de período usam
`date_from` e `date_to` em `AAAA-MM-DD` inclusivos; `date_from > date_to`
retorna `400`. Filtros comuns: `type`, `status`, `task_status` e `role`.

### `GET /reports/dashboard`

- **Query:** `low_stock_threshold` inteiro `>= 0` (padrão `10`) e filtros comuns.
- **Exemplo:** `GET /reports/dashboard?low_stock_threshold=15&date_from=2026-11-01&date_to=2026-11-30`
- **Sucesso `200`:** `DashboardResponse` com `filters`, contagens `orders`, `tasks`, posição atual de `stock`/itens abaixo do limite e resumo de `optimization`.
- **Erros:** `400` data/período/query inválidos; `401`.
- OPERADOR recebe tarefas e otimizações limitadas às próprias; pedidos e estoque são globais.

### `GET /reports/orders`

- **Acesso:** `ADMIN`, `GESTOR`.
- **Query:** filtros comuns; `skip` (`0`), `limit` (`100`, intervalo `1..500`).
- **Exemplo:** `GET /reports/orders?type=OUTBOUND&status=PENDING&skip=0&limit=20`
- **Sucesso `200`:** `{"total":1,"skip":0,"limit":20,"items":[{"id":12,"type":"OUTBOUND","status":"PENDING","created_at":"2026-11-13T10:00:00","items_count":1,"total_quantity":2,"tasks_count":1}]}`
- **Erros:** `400` filtro/período/paginação inválidos; `401`; `403`.

### `GET /reports/orders.csv`

- **Acesso:** `ADMIN`, `GESTOR`.
- **Query:** mesmos filtros comuns do relatório de pedidos.
- **Exemplo:** `GET /reports/orders.csv?type=OUTBOUND&date_from=2026-11-01`
- **Sucesso `200`:** `text/csv; charset=utf-8`, download `orders-report.csv`; linhas representam os mesmos pedidos e filtros de `/reports/orders`.
- **Erros:** `400` filtro/período inválidos; `401`; `403`.

### `GET /reports/stock-movements`

- **Acesso:** `ADMIN`, `GESTOR`.
- **Query:** `product_id` opcional, filtros comuns, `skip` (`0`), `limit` (`100`, intervalo `1..500`).
- **Exemplo:** `GET /reports/stock-movements?product_id=1&type=OUTBOUND&skip=0&limit=20`
- **Sucesso `200`:** `{"total":1,"total_inbound":0,"total_outbound":2,"net_quantity":-2,"skip":0,"limit":20,"items":[{"order_id":12,"order_item_id":31,"movement_type":"OUTBOUND","order_status":"PENDING","created_at":"2026-11-13T10:00:00","product_id":1,"sku":"PROD-001","product_name":"Monitor LED 24\"","quantity":2,"signed_quantity":-2}]}`
- **Erros:** `400` filtro/período/paginação inválidos; `401`; `403`.

### `GET /reports/stock-movements.csv`

- **Acesso:** `ADMIN`, `GESTOR`.
- **Query:** `product_id` opcional e filtros comuns.
- **Exemplo:** `GET /reports/stock-movements.csv?product_id=1&date_from=2026-11-01`
- **Sucesso `200`:** CSV `stock-movements-report.csv` com os mesmos filtros do relatório JSON.
- **Erros:** `400` filtro/período inválidos; `401`; `403`.

## Otimização (`/optimization/*`)

Todas as rotas abaixo exigem autenticação; não há restrição adicional de role
no router. O motor usa distância Manhattan, Nearest Neighbor e 2-opt. As
rotas `POST` registram histórico associado ao usuário; uma falha ao persistir
o histórico não cancela a resposta da otimização.

### `POST /optimization/route`

- **Body:** `locations` (lista de `{id,x,y}` na ordem original; padrão vazia) e `start` opcional (padrão `{id:"START",x:0,y:0}`).
- **Exemplo:** `{"start":{"id":"START","x":0,"y":0},"locations":[{"id":"A1-01-A","x":1,"y":1},{"id":"A1-02-A","x":1,"y":2}]}`
- **Sucesso `200`:** `{"original_route":["START","A1-01-A","A1-02-A"],"nearest_neighbor_route":["START","A1-01-A","A1-02-A"],"two_opt_route":["START","A1-01-A","A1-02-A"],"distance_before":3.0,"nearest_neighbor_distance":3.0,"two_opt_distance":3.0,"distance_after":3.0,"distance_reduction":0.0,"reduction_percent":0.0,"execution_time_ms":1.0,"locations_count":2}`. `execution_time_ms` é variável.
- **Erros:** `400` dados não aceitos pelo motor; `401`.

### `POST /optimization/route/by-order`

- **Body:** `order_id` inteiro `>= 1`; `start` opcional, com o mesmo formato e padrão de `/route`.
- **Exemplo:** `{"order_id":12,"start":{"id":"START","x":0,"y":0}}`
- **Sucesso `200`:** `RouteOptimizeResponse`, no mesmo formato de `/optimization/route`.
- **Erros:** `400` body/dados não aceitos pelo motor; `401`; `404` pedido inexistente, não `OUTBOUND` ou sem posições elegíveis para picking.

### `GET /optimization/reports/summary`

- **Entrada:** sem query/body.
- **Sucesso `200`:** `{"runs_count":3,"average_distance_reduction":2.5,"average_reduction_percent":18.0}`; valores são agregados do histórico.
- **Erros:** `401`.

### `GET /optimization/reports/picking`

- **Entrada:** sem query/body.
- **Sucesso `200`:** lista de execuções com `id`, `user_id`, `user_email`, `executed_at`, `source`, `order_id`, as três rotas, distâncias, reduções e `locations_count`.
- **Erros:** `401`.

### `GET /optimization/reports/picking.csv`

- **Entrada:** sem query/body.
- **Sucesso `200`:** CSV `picking-report.csv`; inclui dados da execução, usuário, pedido, rotas e métricas.
- **Erros:** `401`.

### `GET /optimization/orders/{order_id}/pick-locations`

- **Entrada:** path `order_id`.
- **Exemplo:** `GET /optimization/orders/12/pick-locations`
- **Sucesso `200`:** `[{"id":"A1-01-A","x":1.0,"y":1.0},{"id":"A1-02-A","x":1.0,"y":2.0}]` — posições derivadas de estoque positivo e ativo dos itens do pedido.
- **Erros:** `400` path inválido; `401`; `404` pedido inexistente, não `OUTBOUND` ou sem posições disponíveis.

## Correspondência com o OpenAPI

O OpenAPI é gerado pela aplicação e inclui os métodos e schemas registrados
pelos routers; esta referência detalha as regras de autenticação/roles e erros
implementadas nos handlers. A resposta de validação customizada (`400`, com
`detail` e `errors`) está alinhada com o Swagger. Consulte
[`S10-openapi-paths.txt`](./sprint-10/evidencias/S10-openapi-paths.txt) e
[`S10-openapi-validation.txt`](./sprint-10/evidencias/S10-openapi-validation.txt)
para o snapshot executado na Sprint 10.

Os endpoints `/products`, `/stock`, `/locations` e `/optimization-results`
também constam no OpenAPI, mas não fazem parte dos grupos detalhados neste
recorte; use `/docs` para seus contratos atuais.
