# Contrato da API de Métricas e Especificação — Motor de Otimização

**Endpoint:** `POST /optimization/route`  
**Módulo:** Pessoa 3 (Motor de Otimização)  
**Status dos Testes:** 100% Verdes (9/9 passados)

---

## 1. Algoritmos Utilizados

O motor utiliza uma abordagem combinada em duas etapas para calcular a rota otimizada de coleta (*picking*):

1. **Heurística Construtiva — Vizinho Mais Próximo (*Nearest Neighbor*):** Gera uma solução inicial determinística ao conectar iterativamente o ponto atual ao local mais próximo ainda não visitado.
2. **Heurística de Refinamento Local — 2-opt:** Aplica trocas de arestas cruzadas sobre a rota inicial até alcançar um ótimo local, eliminando cruzamentos e reduzindo a distância total percorrida.

---

## 2. Fluxo de Integração de Dados (Pipeline para a Sprint 06)

Para a integração completa com o módulo de Pedidos e Estoque, o fluxo de transformação de dados segue a cadeia:

`Pedido` ➔ `Itens do Pedido` ➔ `Produtos` ➔ `Posições no Estoque (x, y)` ➔ `Rota Otimizada`

1. **Pedido:** O frontend ou backend seleciona um ou mais pedidos ativos.
2. **Itens & Produtos:** O sistema recupera a lista de SKUs/produtos vinculados aos pedidos.
3. **Posições:** O mapa do estoque converte as localizações físicas dos produtos em coordenadas cartesianas (`x`, `y`).
4. **Motor de Otimização:** As posições convertidas são enviadas ao endpoint `POST /optimization/route`.
5. **Rota Otimizada:** O endpoint retorna a sequência ideal de coleta e as métricas de ganho de eficiência.

---

## 3. Payload de Entrada (Request)

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

4. Resposta de Sucesso (Response - 200 OK)

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

5. Descrição dos Campos para o Frontend

original_route (Array de Strings): Sequência original dos pontos sem otimização.

locations_count (Inteiro): Total de locais a visitar na rota.

distance_before (Decimal / Float): Distância percorrida na rota não otimizada.

distance_after (Decimal / Float): Distância final após a otimização (2-opt).

nearest_neighbor_distance (Decimal / Float): Distância calculada pelo Vizinho Mais Próximo.

two_opt_distance (Decimal / Float): Distância final otimizada pelo 2-opt.

distance_reduction (Decimal / Float): Distância economizada (calculada por distance_before - distance_after).

reduction_percent (Decimal / Float): Percentual de redução da distância percorrida (%).

execution_time_ms (Decimal / Float): Tempo de processamento do algoritmo em milissegundos.