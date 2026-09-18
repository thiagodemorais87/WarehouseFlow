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
- Integração com pedidos reais no banco ainda é futura (`OrderRouteProvider`).

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
| `POST /optimization/route/by-order` | Integração futura (não bloqueia esta sprint) |
| `GET /health` | Implementado |

## 15. Integração (Pessoa 1 — banco/backend)

1. Modelar `Position(x, y, code)`, `Order`, `OrderItem`, estoque.
2. Implementar `OrderRouteProvider.get_pick_locations(order_id)` com SQLAlchemy.
3. No service, se vier `order_id`, obter `list[Location]` e chamar `optimize_route`.
4. Frontend chama `POST /optimization/route` (ou futuro by-order) e exibe rotas/métricas.

O núcleo em `backend/optimization/` permanece inalterado.
