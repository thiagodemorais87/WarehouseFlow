# Manual Técnico — WarehouseFlow

**Projeto:** WarehouseFlow (Grupo 26)  
**Foco deste documento (Sprint 11):** componente de otimização / motor de picking  
**Responsável pelo módulo:** Thiago de Morais Gonçalves (Pessoa 3 — Motor)

> Outras seções do sistema (auth, produtos, pedidos, deploy) podem ser complementadas pela equipe.  
> Detalhe profundo do algoritmo: [`docs/optimization.md`](optimization.md) · Contrato FE: [`docs/contrato_api_otimizacao.md`](contrato_api_otimizacao.md).

---

## Registro técnico da Sprint 09 — QA e correção

O documento formal dos testes de QA está em
[`sprint-9/matriz_testes_sprint9.md`](sprint-9/matriz_testes_sprint9.md).
A cobertura de navegação e acesso está em
[`sprint-9/testes_navegacao_permissoes.md`](sprint-9/testes_navegacao_permissoes.md).

A aplicação implementa `ADMIN`, `GESTOR` e `OPERADOR`. A autenticação aceita
JWT no cabeçalho `Authorization: Bearer` ou cookie `access_token`; as páginas
HTML verificam a sessão no backend e redirecionam para `/login` sem usuário.
As restrições administrativas são aplicadas no backend e complementadas por
`data-roles` no menu.

Na correção registrada como BUG-S9-01, `DELETE /products/{product_id}` passou
a consultar dependências em `stock` e `order_items`. Referências existentes
produzem `409 Conflict`; a exclusão sem dependências continua retornando
`204 No Content`.

## 1. Componente de otimização (diferencial)

### 1.1 Visão geral

O diferencial computacional do WarehouseFlow **não é IA generativa nem ML**. É um motor heurístico clássico que sequencia a visita às posições de picking:

1. **Nearest Neighbor (NN)** — constrói uma rota gulosa a partir do ponto `START`.
2. **2-opt** — refinamento local que **nunca piora** a rota NN.
3. Comparação honesta com a **rota original** (ordem dos itens / entrada).

Distância: **Manhattan** `|Δx| + |Δy|` (grade de corredores).

Pacote puro (sem FastAPI/DB): `backend/optimization/` → função pública `optimize_route`.

### 1.2 Arquitetura

```text
UI (/otimizacao, dashboard, relatórios)
        │ JWT
        ▼
FastAPI  /optimization/*          ← oficial
        │
        ├─ POST /route              → locations no body
        ├─ POST /route/by-order     → SqlAlchemyOrderRouteProvider(order_id)
        │                              OUTBOUND → stock → location → (x,y)
        │
        ▼
  optimization.engine (NN → 2-opt + métricas)
        │
        ▼
  optimization_runs (best-effort)  ← histórico oficial
```

| Camada | Arquivos principais |
|--------|---------------------|
| Núcleo | `backend/optimization/engine.py`, `nearest_neighbor.py`, `two_opt.py`, `distance.py`, `types.py` |
| API | `backend/app/routers/optimization_engine.py` |
| Service / providers | `optimization_service.py`, `providers/sqlalchemy.py`, `providers/coords.py` |
| Persistência oficial | `optimization_runs` · ORM `models/optimization_run.py` |
| UI | `frontend/templates/optimization/`, `static/js/optimization.js` |

### 1.3 Oficial vs legado

| Caminho | Status | Função |
|---------|--------|--------|
| `/optimization/*` + `optimization_runs` | **Oficial** | Pipeline do motor; UI e relatórios |
| `/optimization-results` + `optimization_results` | **Legado (deprecated)** | CRUD por `task_id`; **não** alimentado pelo NN+2-opt |

Falha ao gravar `optimization_runs` **não** interrompe a otimização (HTTP 200); o erro é **logado** no recorder.

### 1.4 Algoritmos (resumo)

| Etapa | Comportamento |
|-------|----------------|
| Distância | Manhattan entre pontos consecutivos da rota (incluindo `START`) |
| NN | Sempre escolhe o vizinho mais próximo ainda não visitado; empate por `id` |
| 2-opt | Trocas de arestas que reduzam distância; nunca aumenta a distância NN |
| Original | Ordem exata da lista de `locations` de entrada |

### 1.5 Métricas obrigatórias

Todas calculadas (nunca inventadas):

| Campo | Significado |
|-------|-------------|
| `original_route` / `nearest_neighbor_route` / `two_opt_route` | Sequências de IDs |
| `distance_before` | Distância da rota original |
| `nearest_neighbor_distance` | Após NN |
| `two_opt_distance` / `distance_after` | Após 2-opt (`after == two_opt`) |
| `distance_reduction` | `before - after` (pode ser ≤ 0) |
| `reduction_percent` | `%` de redução; `0` se `before == 0` |
| `execution_time_ms` | Tempo do pipeline |
| `locations_count` | Posições (sem `START`) |

### 1.6 Endpoints oficiais

| Método | Path | Uso |
|--------|------|-----|
| `POST` | `/optimization/route` | Coordenadas no body |
| `POST` | `/optimization/route/by-order` | `order_id` OUTBOUND |
| `GET` | `/optimization/orders/{id}/pick-locations` | Helper de posições |
| `GET` | `/optimization/reports/summary` | KPI (dashboard) |
| `GET` | `/optimization/reports/picking` | Histórico JSON |
| `GET` | `/optimization/reports/picking.csv` | Export CSV |

Auth: JWT em todos. Detalhe de payloads: [`contrato_api_otimizacao.md`](contrato_api_otimizacao.md).

### 1.7 Como verificar o motor

```powershell
# Suite automatizada (na raiz do repo)
python -m pytest tests/test_api_optimization.py tests/test_optimization_flow_integration.py tests/test_optimization_reports.py tests/test_engine.py tests/test_distance.py tests/test_nearest_neighbor.py tests/test_two_opt.py -q

# Evidência ponta a ponta (SQLite em memória + TestClient)
$env:PYTHONPATH = "backend"
python -m optimization.evidence_flow
```

Fixture clássica do evidence: `distance_before=38` → `distance_after=11` (~71% de redução).

Ambiente com UI:

```powershell
docker compose up --build
```

- UI: http://127.0.0.1:8080/otimizacao  
- Swagger: http://127.0.0.1:8000/docs  
- Login seed: `admin@warehouseflow.com` / `admin123`

### 1.8 Referências

| Documento | Conteúdo |
|-----------|----------|
| [`optimization.md`](optimization.md) | Manual profundo (algoritmos, contrato, integração) |
| [`contrato_api_otimizacao.md`](contrato_api_otimizacao.md) | Contrato estável FE |
| [`backend/optimization/README.md`](../backend/optimization/README.md) | Uso isolado do pacote |
| [`backend/database/README.md`](../backend/database/README.md) | DDL oficial vs legado |
| `docs/sprint-11/` | Evidências Sprint 11 do motor |
