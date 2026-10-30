# Contrato da API — Motor de Otimização (estável para o frontend)

**Módulo:** Pessoa 3 (Motor de Otimização)  
**Prefixo:** `/optimization`  
**Auth:** JWT em todos os endpoints abaixo  

Histórico é gravado **implicitamente** em `POST /optimization/route` e `POST /optimization/route/by-order`.  
Não existe `POST /optimization/history`.

---

## 1. Algoritmos

1. **Nearest Neighbor** — rota inicial gulosa.
2. **2-opt** — refinamento local (nunca piora a rota NN).

Distância: Manhattan `|Δx| + |Δy|`.

---

## 2. Pipeline por pedido

`Pedido OUTBOUND` → itens → stock → location → `(x,y)` derivados → NN + 2-opt → `RouteOptimizeResponse` → grava `optimization_runs` (best-effort).

---

## 3. `POST /optimization/route`

### Request

```json
{
  "start": { "id": "START", "x": 0, "y": 0 },
  "locations": [
    { "id": "FAR1", "x": 10, "y": 0 },
    { "id": "NEAR1", "x": 1, "y": 0 },
    { "id": "FAR2", "x": 11, "y": 0 },
    { "id": "NEAR2", "x": 2, "y": 0 }
  ]
}
```

- `locations` pode ser `[]` → distâncias 0, HTTP 200.
- `start` default: `START (0, 0)`.

### Response 200 — `RouteOptimizeResponse` (contrato FE)

Campos obrigatórios (não remover / não renomear):

| Campo | Tipo | Uso no FE |
|-------|------|-----------|
| `original_route` | `string[]` | Exibir rota original |
| `nearest_neighbor_route` | `string[]` | Exibir rota NN |
| `two_opt_route` | `string[]` | Rota principal na UI |
| `distance_before` | `float` | Distância original |
| `nearest_neighbor_distance` | `float` | Distância NN |
| `two_opt_distance` | `float` | Distância 2-opt |
| `distance_after` | `float` | Alias de `two_opt_distance` |
| `distance_reduction` | `float` | `before - after` (pode ser ≤ 0) |
| `reduction_percent` | `float` | 0 se `before == 0` |
| `execution_time_ms` | `float` | Tempo do algoritmo |
| `locations_count` | `int` | Posições (sem START) |

### Erros

| Código | Quando |
|--------|--------|
| `400` | IDs duplicados em `locations` (detalhe contém "duplicado") |
| `401` | Sem JWT válido |

---

## 4. `POST /optimization/route/by-order`

### Request

```json
{ "order_id": 1, "start": { "id": "START", "x": 0, "y": 0 } }
```

### Response 200

Mesmo `RouteOptimizeResponse` da seção 3. Grava histórico com `source="by-order"` e `order_id`.

### Erros

| Código | Quando |
|--------|--------|
| `404` | Pedido inexistente, não OUTBOUND, ou sem posições de picking |
| `400` | IDs duplicados (após resolução do provider — raro; provider deduplica por code) |
| `401` | Sem JWT válido |

---

## 5. Histórico e relatórios

### `GET /optimization/reports/summary` — `OptimizationSummaryResponse`

| Campo | Tipo | Uso no FE |
|-------|------|-----------|
| `runs_count` | `int` | KPI quantidade |
| `average_distance_reduction` | `float` | KPI redução média absoluta |
| `average_reduction_percent` | `float` | KPI redução média % (dashboard / picking) |

Sem filtros de data/usuário (médias globais das execuções gravadas).

### `GET /optimization/reports/picking` — `OptimizationRunResponse[]`

Ordenado do mais recente ao mais antigo. Campos do schema (completos):

`id`, `user_id`, `user_email`, `executed_at`, `source`, `order_id`,  
`original_route`, `nearest_neighbor_route`, `two_opt_route`,  
`distance_before`, `nearest_neighbor_distance`, `two_opt_distance`,  
`distance_after`, `distance_reduction`, `reduction_percent`,  
`execution_time_ms`, `locations_count`

Campos lidos pela tabela do FE (`picking-report.js`):  
`executed_at`, `user_id`, `order_id`, `source`, `locations_count`,  
`distance_before`, `distance_after`, `reduction_percent`, `execution_time_ms`, `two_opt_route`.

### `GET /optimization/reports/picking.csv`

- `Content-Type: text/csv`
- `Content-Disposition: attachment; filename=picking-report.csv`
- Rotas no CSV: ids unidos por ` > `
- Colunas: mesmas do picking JSON (flat)

---

## 6. Helper

### `GET /optimization/orders/{order_id}/pick-locations`

Lista `{id, x, y}` na ordem dos itens. `404` se o provider falhar (mesmo critério do by-order).

---

## 7. Regras do motor (resumo)

| Regra | Comportamento |
|-------|----------------|
| IDs duplicados no body | HTTP 400 |
| Pedido sem posições / inexistente / INBOUND | HTTP 404 |
| Métricas | `distance_after == two_opt_distance`; redução coerente; 2-opt ≤ NN |
| Falha ao gravar `optimization_runs` | Otimização ainda retorna 200; histórico simplesmente não aparece nos reports |

---

## 8. DDL do histórico

Tabela `optimization_runs`: ver [`backend/database/optimization_runs.sql`](../backend/database/optimization_runs.sql).
