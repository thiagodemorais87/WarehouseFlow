# Motor de Otimização — Sequenciamento de Picking

Documentação técnica do diferencial computacional do **WarehouseFlow** (Sprint de otimização).

## 1. Problema

Dado um pedido com vários produtos em posições distintas do armazém, calcular uma **sequência de visita** às posições que reduza o deslocamento do operador durante o picking.

Formalmente: partindo de um ponto `START`, visitar cada posição exatamente uma vez, minimizando a distância total percorrida.

## 2. Contexto no WarehouseFlow

O sistema gerencia produtos, estoque, pedidos e posições. O motor **não substitui** o CRUD: ele consome localizações (coordenadas `x`, `y`) e devolve uma rota sugerida com métricas.

Nesta versão, o motor é **desacoplado** do PostgreSQL. A API aceita localizações no body; a integração `order_id → posições` fica para sprints futuras.

## 3. Objetivo

- Construir uma rota inicial com heurística **Nearest Neighbor**.
- Refinar com melhoria local **2-opt**.
- Comparar com a **rota original** (ordem dos itens / ordem de entrada).
- Expor métricas calculadas (nunca valores inventados).

## 4. Entrada

Lista de posições e ponto inicial:

```json
{
  "locations": [
    {"id": "A01", "x": 1, "y": 1},
    {"id": "C03", "x": 5, "y": 5},
    {"id": "B02", "x": 2, "y": 2},
    {"id": "D04", "x": 8, "y": 3}
  ],
  "start": {"id": "START", "x": 0, "y": 0}
}
```

A **rota original** é exatamente a ordem de `locations`.

## 5. Saída

- `original_route`, `nearest_neighbor_route`, `two_opt_route`
- `distance_before`, `nearest_neighbor_distance`, `two_opt_distance`, `distance_after`
- `distance_reduction`, `reduction_percent`
- `execution_time_ms`, `locations_count`

## 6. Distância Manhattan

```text
distance(A, B) = |xA - xB| + |yA - yB|
```

Adequada a deslocamento em grade/corredores (sem diagonais livres).

Distância total da rota:

```text
START → P1 → P2 → … → PN
```

## 7. Nearest Neighbor (Vizinho Mais Próximo)

1. Posição atual = `START`.
2. Enquanto houver posições não visitadas, escolher a de menor distância Manhattan à atual.
3. Empate: menor `id` (determinismo).
4. Avançar para a escolhida e repetir.

**Complexidade:** O(N²).

Não garante ótimo global. Em layouts específicos pode produzir rota pior que a ordem original — o sistema **reporta isso**.

## 8. 2-opt

A partir da rota NN, tenta inverter segmentos `i..j`. Se a distância total diminuir, aceita. Repete até não haver melhoria.

**Garantia local:** `two_opt_distance <= nearest_neighbor_distance`.

**Não garante:** `two_opt_distance <= distance_before`.

**Complexidade:** O(N²) por passagem; número de passagens limitado pela estabilização.

## 9. Métricas

```text
distance_reduction = distance_before - distance_after

reduction_percent =
  0                           se distance_before == 0
  (distance_reduction / distance_before) * 100   caso contrário
```

`distance_after` = `two_opt_distance`.

## 10. Complexidade e natureza heurística

O sequenciamento de visitas é da família de problemas de **roteamento / ordenação combinatória** (caminho tipo TSP). O número de permutações é N!.

Busca exaustiva é inviável para N moderado/alto. Por isso usamos **heurística**:

- rápida;
- implementável sem solver externo;
- suficiente para demonstrar ganho operacional em casos típicos;
- resultados interpretáveis (rota + métricas).

Não usamos OR-Tools, NetworkX nem solvers comerciais: o diferencial acadêmico é a **implementação própria** da lógica NN + 2-opt, integrada ao sistema.

## 11. Limitações

- Não considera capacidade de carrinho, janelas de tempo, corredores unidirecionais ou obstáculos.
- Uma visita por posição; não modela múltiplas unidades no mesmo ponto além da própria posição.
- Heurística: não garante ótimo global.
- Rota final pode ser pior que a original em casos patológicos (reportado honestamente).
- Integração com pedidos reais no banco ainda é futura (`SqlAlchemyOrderRouteProvider` na Sprint 06).
  Na Sprint 05 existe ponte via `MemoryOrderRouteProvider` + `POST /optimization/route/by-order`.
- IDs de posição duplicados são rejeitados com erro (HTTP 400 na API).

## 12. Exemplo (fixture acadêmica)

Ordem deliberadamente ruim (longe/perto intercalados):

```text
START(0,0) → FAR1(10,0) → NEAR1(1,0) → FAR2(11,0) → NEAR2(2,0)
```

O pipeline NN + 2-opt reorganiza a visita e **calcula** redução real. Execute:

```bash
python -c "from optimization.engine import optimize_route; from optimization.types import Location; ..."
```

ou `POST /optimization/route` com o mesmo payload. Os números saem do algoritmo, não de constantes.

## 13. Estratégia de testes

Pytest determinístico (sem aleatoriedade):

- Manhattan e distância total
- Rota original preserva ordem
- Nearest Neighbor (incluindo empate por `id`)
- 2-opt não piora a rota de entrada
- Métricas e divisão por zero (`distance_before == 0`)
- 0, 1 e N posições
- Fixture acadêmica com redução real
- API `POST /optimization/route`

```bash
pip install -r requirements.txt
pytest -q
```

## 14. Endpoints

| Endpoint | Status |
|----------|--------|
| `POST /optimization/route` | Implementado (locations no body) |
| `POST /optimization/route/by-order` | Implementado na Sprint 05 (MemoryProvider; Postgres na S06) |
| `GET /optimization/orders/{order_id}/pick-locations` | Implementado na Sprint 05 (helper para S06) |
| `GET /health` | Implementado |

---

## 15. Contrato da API para o frontend (Sprint 05/06)

Documento de referência para a Pessoa 4 (front) consumir o motor sem adivinhar campos.  
Schemas: `backend/app/schemas/optimization.py` · Rota: `backend/app/routers/optimization_engine.py` · Swagger: `/docs`.

### 15.1 Método e URL

```http
POST /optimization/route
Content-Type: application/json
Authorization: Bearer <access_token>
```

Requer autenticação JWT (`POST /auth/login`). Não depende do PostgreSQL para o cálculo da rota.

### 15.2 Request (body)

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `locations` | `array` | sim (pode ser `[]`) | Posições a visitar, **na ordem original** do pedido/itens |
| `locations[].id` | `string` | sim | Identificador da posição (ex.: `A01`) |
| `locations[].x` | `number` | sim | Coordenada X (grade do armazém) |
| `locations[].y` | `number` | sim | Coordenada Y |
| `start` | `object` | não | Ponto de partida; default `{ "id": "START", "x": 0, "y": 0 }` |
| `start.id` | `string` | se enviar `start` | Id do ponto inicial |
| `start.x` / `start.y` | `number` | se enviar `start` | Coordenadas do ponto inicial |

IDs de posição devem ser **únicos** no array; duplicados retornam HTTP 400.

### 15.3 Response (JSON)

| Campo | Tipo | Significado para a UI |
|-------|------|------------------------|
| `original_route` | `string[]` | Ordem de visita **antes** da otimização (`START` + ids na ordem de entrada) |
| `nearest_neighbor_route` | `string[]` | Rota após heurística Nearest Neighbor |
| `two_opt_route` | `string[]` | Rota **sugerida** após 2-opt — **usar esta como rota principal na tela** |
| `distance_before` | `number` | Distância Manhattan da rota original |
| `nearest_neighbor_distance` | `number` | Distância após NN |
| `two_opt_distance` | `number` | Distância após 2-opt |
| `distance_after` | `number` | Sempre igual a `two_opt_distance` (alias para a UI) |
| `distance_reduction` | `number` | `distance_before - distance_after` (pode ser ≤ 0 em casos ruins) |
| `reduction_percent` | `number` | Redução percentual; `0` se `distance_before == 0` |
| `execution_time_ms` | `number` | Tempo de execução do algoritmo em milissegundos |
| `locations_count` | `integer` | Quantidade de posições em `locations` (sem contar `START`) |

### 15.4 Regras de UI recomendadas

1. Exibir como rota sugerida: `two_opt_route` (não a NN isolada).
2. Comparar “antes × depois” com `original_route` vs `two_opt_route` e `distance_before` vs `distance_after`.
3. Mostrar ganho com `distance_reduction` e `reduction_percent` (formatar `%` com 1–2 casas).
4. Se `distance_reduction < 0`, avisar que a heurística não melhorou a ordem original (comportamento válido).
5. Garantia do backend: `two_opt_distance <= nearest_neighbor_distance`.
6. Garantia do backend: `distance_after === two_opt_distance`.

### 15.5 Exemplo de request

```json
{
  "locations": [
    {"id": "FAR1", "x": 10, "y": 0},
    {"id": "NEAR1", "x": 1, "y": 0},
    {"id": "FAR2", "x": 11, "y": 0},
    {"id": "NEAR2", "x": 2, "y": 0}
  ],
  "start": {"id": "START", "x": 0, "y": 0}
}
```

### 15.6 Exemplo de response (formato)

```json
{
  "original_route": ["START", "FAR1", "NEAR1", "FAR2", "NEAR2"],
  "nearest_neighbor_route": ["START", "NEAR1", "NEAR2", "FAR1", "FAR2"],
  "two_opt_route": ["START", "NEAR1", "NEAR2", "FAR1", "FAR2"],
  "distance_before": 34.0,
  "nearest_neighbor_distance": 14.0,
  "two_opt_distance": 14.0,
  "distance_after": 14.0,
  "distance_reduction": 20.0,
  "reduction_percent": 58.82352941176471,
  "execution_time_ms": 0.12,
  "locations_count": 4
}
```

> Os números exatos de distância/tempo vêm do algoritmo; o front não deve hardcodar métricas.

### 15.7 Smoke com curl

```bash
# 1) Login
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"admin@warehouseflow.com\",\"password\":\"admin123\"}" \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2) Otimizar rota
curl -s -X POST http://127.0.0.1:8000/optimization/route \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"locations\":[{\"id\":\"A01\",\"x\":1,\"y\":1},{\"id\":\"C03\",\"x\":5,\"y\":5}],\"start\":{\"id\":\"START\",\"x\":0,\"y\":0}}"
```

### 15.8 Limitações do endpoint `/route`

- Este endpoint **não** aceita `order_id` — o front envia coordenadas explícitas.
- Para otimizar a partir de pedido, use `POST /optimization/route/by-order` (seção 17).
- Distância é **Manhattan**; não é km reais de GPS.

---

## 16. Integração (Pessoa 1 — banco/backend)

Na Sprint 05 o by-order usa `MemoryOrderRouteProvider`. Para a Sprint 06:

1. Adicionar colunas `x`, `y` em `locations` (migration alinhada ao CRUD de posições).
2. Implementar `SqlAlchemyOrderRouteProvider.get_pick_locations(order_id)`:
   - pedido `OUTBOUND` → `order_items` → produto → `stock` → `location` `(code, x, y)`;
   - ordem das posições = ordem dos itens; deduplicar por `location.code` se o mesmo produto aparecer mais de uma vez.
3. Substituir o provider injetado em `optimization_engine.py` (mesmo service `optimize_from_order_id`).
4. Frontend chama `POST /optimization/route/by-order` e exibe rotas/métricas conforme a seção 15.

O núcleo em `backend/optimization/` permanece inalterado.

---

## 17. Contrato `order_id` (preparação Sprint 06)

Documento de ponte da Sprint 05: permite testar o fluxo pedido → posições → rota **sem** depender ainda de `x`/`y` no PostgreSQL.

### 17.1 Fluxo alvo (S06) vs ponte atual (S05)

```text
Pedido OUTBOUND
  → order_items (produto + quantidade)
    → stock / location (code, x, y)
      → list[Location]
        → optimize_route (NN + 2-opt)
          → RouteOptimizeResponse
```

| Etapa | Sprint 05 | Sprint 06 |
|-------|-----------|-----------|
| Fonte das posições | `MemoryOrderRouteProvider` (catálogo acadêmico) | `SqlAlchemyOrderRouteProvider` + Postgres |
| Coordenadas | Fixture em memória (`order_id` 1 e 2) | Colunas `locations.x` / `locations.y` |
| Tipo de pedido | Implícito no catálogo | Apenas **OUTBOUND** (picking); INBOUND fora do escopo |

Catálogo acadêmico default:

| `order_id` | Posições (ordem original) |
|------------|---------------------------|
| `1` | FAR1(10,0), NEAR1(1,0), FAR2(11,0), NEAR2(2,0) |
| `2` | A01(1,1), C03(5,5), B02(2,2), D04(8,3) |

### 17.2 `POST /optimization/route/by-order`

```http
POST /optimization/route/by-order
Content-Type: application/json
Authorization: Bearer <access_token>
```

**Request**

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `order_id` | `integer` (≥ 1) | sim | ID do pedido no catálogo / banco |
| `start` | `object` | não | Mesmo formato de `/route`; default START (0,0) |

**Response:** idêntico a `RouteOptimizeResponse` (seção 15.3).

**Erros**

| HTTP | Quando |
|------|--------|
| `404` | Pedido ausente no provider (`Pedido {id} não encontrado no catálogo de picking`) |
| `400` | IDs de posição duplicados (ou payload inválido) |
| `401` | Sem JWT válido |

**Exemplo**

```json
{ "order_id": 1, "start": { "id": "START", "x": 0, "y": 0 } }
```

```bash
curl -s -X POST http://127.0.0.1:8000/optimization/route/by-order \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"order_id\":1}"
```

### 17.3 `GET /optimization/orders/{order_id}/pick-locations`

Helper para o front / integração S06: lista as posições **antes** de otimizar.

```http
GET /optimization/orders/1/pick-locations
Authorization: Bearer <access_token>
```

**Response (200)**

```json
[
  {"id": "FAR1", "x": 10.0, "y": 0.0},
  {"id": "NEAR1", "x": 1.0, "y": 0.0},
  {"id": "FAR2", "x": 11.0, "y": 0.0},
  {"id": "NEAR2", "x": 2.0, "y": 0.0}
]
```

**404** se o pedido não existir no catálogo.

O front pode: (1) chamar este GET e depois `POST /optimization/route`, ou (2) chamar direto `POST /optimization/route/by-order`.

### 17.4 Regras de negócio (motor / picking)

1. Escopo de otimização: pedidos **OUTBOUND** (picking). INBOUND / putaway ficam fora deste contrato.
2. Ordem original da rota = ordem dos itens / posições retornadas pelo provider.
3. Cada posição aparece uma vez (`id` único); o motor rejeita duplicados.
4. Métricas nunca são inventadas — sempre calculadas pelo pipeline NN + 2-opt.
5. Na S05 o catálogo é em memória; evidências de “pedido real no banco → rota” exigem S06 + `x`/`y` em `locations`.

### 17.5 Código de referência

| Peça | Arquivo |
|------|---------|
| Protocolo | `backend/app/providers/base.py` |
| Provider S05 | `backend/app/providers/memory.py` |
| Service | `backend/app/services/optimization_service.py` (`optimize_from_order_id`) |
| Router | `backend/app/routers/optimization_engine.py` |
| Schemas | `RouteOptimizeByOrderRequest`, `PickLocationResponse` |
| Testes | `tests/test_memory_provider.py`, `tests/test_api_optimization.py` |
