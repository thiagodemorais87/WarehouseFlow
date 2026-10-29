# Motor de otimização de picking (uso isolado)

Pacote **puro Python** — sem FastAPI, SQLAlchemy ou PostgreSQL.

## Instalação

Na raiz do repositório:

```bash
pip install -r requirements.txt
```

Garanta que `backend/` esteja no `PYTHONPATH` (o `pytest.ini` já configura isso para os testes).

## Uso programático

```python
from optimization import Location, optimize_route

locations = [
    Location(id="FAR1", x=10, y=0),
    Location(id="NEAR1", x=1, y=0),
    Location(id="FAR2", x=11, y=0),
    Location(id="NEAR2", x=2, y=0),
]
start = Location(id="START", x=0, y=0)

result = optimize_route(locations, start=start)

print("Rota original:", " → ".join(result.original_route))
print("Distância original:", result.distance_before)
print("Nearest Neighbor:", " → ".join(result.nearest_neighbor_route))
print("Distância NN:", result.nearest_neighbor_distance)
print("Após 2-opt:", " → ".join(result.two_opt_route))
print("Distância otimizada:", result.two_opt_distance)
print("Redução:", result.distance_reduction)
print("Redução %:", result.reduction_percent)
print("Tempo ms:", result.execution_time_ms)
print("Posições:", result.locations_count)
```

## Pipeline

1. **Rota original** — ordem da lista de entrada (ex.: ordem dos itens do pedido).
2. **Nearest Neighbor** — constrói rota gulosa.
3. **2-opt** — melhora local a partir da rota NN.

Distâncias usam Manhattan: `|Δx| + |Δy|`.

## Métricas

| Campo | Significado |
|-------|-------------|
| `distance_before` | Distância da rota original |
| `nearest_neighbor_distance` | Distância após NN |
| `two_opt_distance` / `distance_after` | Distância após 2-opt |
| `distance_reduction` | `before - after` (pode ser ≤ 0) |
| `reduction_percent` | 0 se `before == 0`; senão `(reduction / before) * 100` |

O 2-opt **nunca piora** a rota NN. A rota final **pode** ser pior que a original — o motor reporta isso honestamente.

## Integração com a API

A API FastAPI adapta JSON → `Location` e chama `optimize_route`:

| Endpoint | Descrição |
|----------|-----------|
| `POST /optimization/route` | Body com `locations` explícitas |
| `POST /optimization/route/by-order` | `order_id` → provider → mesmo motor |
| `GET /optimization/orders/{id}/pick-locations` | Lista posições do pedido (helper) |
| `GET /optimization/reports/summary` | `runs_count` + redução média |
| `GET /optimization/reports/picking` | Histórico das execuções |
| `GET /optimization/reports/picking.csv` | Export CSV do picking |

`POST /optimization/route/by-order` usa `SqlAlchemyOrderRouteProvider` (OUTBOUND → itens → stock → location).  
Coordenadas `(x, y)` são derivadas de aisle/rack/shelf/code.  
`MemoryOrderRouteProvider` permanece para testes e overrides (pedido sem posições → `KeyError` / HTTP 404).

Histórico: cada otimização bem-sucedida tenta gravar em `optimization_runs`. Falha de persistência **não** quebra o POST (ainda retorna 200).

Contrato estável para o frontend: [`docs/contrato_api_otimizacao.md`](../../docs/contrato_api_otimizacao.md).  
Detalhes técnicos: [`docs/optimization.md`](../../docs/optimization.md).

### DDL do histórico

Arquivo dedicado (só a tabela do motor):

[`backend/database/optimization_runs.sql`](../database/optimization_runs.sql)

### Evidência ponta a ponta

```bash
# Na raiz do repositório
$env:PYTHONPATH = "backend"   # PowerShell; no bash: export PYTHONPATH=backend
python -m optimization.evidence_flow
```

Imprime otimização + summary (redução média) + picking + CSV e sai com código 0 se tudo ok.

### Cenários manuais rápidos

| Cenário | Como |
|---------|------|
| Coordenadas no body (UI atual) | `POST /optimization/route` com `locations` |
| Pedido seed OUTBOUND `id=1` | `POST /optimization/route/by-order` `{"order_id":1}` |
| Listar posições antes de otimizar | `GET /optimization/orders/1/pick-locations` |
| Pedido inexistente / INBOUND / sem posições | HTTP 404 |
| IDs duplicados no body | HTTP 400 |
| 0 posições no body | `locations: []` → distâncias 0 |
| Relatório + CSV | `GET /optimization/reports/summary` e `/picking` / `/picking.csv` |
