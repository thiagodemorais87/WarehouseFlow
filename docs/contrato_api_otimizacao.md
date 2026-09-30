# Contrato da API de Métricas — Motor de Otimização

**Endpoint:** `POST /optimization/route`  
**Módulo:** Pessoa 3 (Motor de Otimização)

---

## 1. Payload de Entrada (Request)

```json
{
  "start": {
    "id": "START",
    "x": 0,
    "y": 0
  },
  "locations": [
    {"id": "FAR1", "x": 10, "y": 0},
    {"id": "NEAR1", "x": 1, "y": 0},
    {"id": "FAR2", "x": 11, "y": 0},
    {"id": "NEAR2", "x": 2, "y": 0}
  ]
}

```
## 2. Resposta de Sucesso (Response - 200 OK)

{
  "original_route": ["START", "FAR1", "NEAR1", "FAR2", "NEAR2"],
  "locations_count": 4,
  "distance_before": 44.0,
  "distance_after": 22.0,
  "nearest_neighbor_distance": 22.0,
  "two_opt_distance": 22.0,
  "distance_reduction": 22.0,
  "reduction_percent": 50.0,
  "execution_time_ms": 0.42
}

3. Descrição dos Campos para o Frontend
original_route (Array de Strings): Sequência original dos pontos sem otimização.

locations_count (Inteiro): Total de locais a visitar na rota.

distance_before (Decimal / Float): Distância percorrida na rota não otimizada.

distance_after (Decimal / Float): Distância final após a otimização (2-opt).

nearest_neighbor_distance (Decimal / Float): Distância calculada pelo Vizinho Mais Próximo.

two_opt_distance (Decimal / Float): Distância final otimizada pelo 2-opt.

distance_reduction (Decimal / Float): Distância economizada (calculada por distance_before - distance_after).

reduction_percent (Decimal / Float): Percentual de redução da distância percorrida (%).

execution_time_ms (Decimal / Float): Tempo de processamento do algoritmo em milissegundos.