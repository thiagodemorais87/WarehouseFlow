# Matriz de otimização — Sprint 10 (Release Candidate)

**Projeto:** WarehouseFlow — Grupo 26  
**Responsável:** Thiago (motor de otimização)  
**Escopo:** evidências de rota, métricas, integração e coerência de `optimization_runs` para a RC.

## Ambiente

- Suíte automatizada: pytest + SQLite em memória / TestClient FastAPI.
- Script ponta a ponta: `python -m optimization.evidence_flow` (`PYTHONPATH=backend`).
- Prints manuais: sistema via Docker Compose (`http://127.0.0.1:8080` ou `:8000`) — checklist abaixo.

## Casos automatizados / script

| ID | Cenário | Como evidenciar | Resultado esperado | Status | Evidência |
|---|---|---|---|---|---|
| S10-OPT-A01 | `POST /optimization/route` com locais | pytest API + evidence_flow | HTTP 200; rotas original / NN / 2-opt; métricas coerentes | PASSOU | [pytest-optimization.txt](./evidencias/pytest-optimization.txt), [evidence-flow.txt](./evidencias/evidence-flow.txt) |
| S10-OPT-A02 | `POST /optimization/route/by-order` | pytest integração / API | HTTP 200 a partir de pedido OUTBOUND com posições | PASSOU | [pytest-optimization.txt](./evidencias/pytest-optimization.txt) |
| S10-OPT-A03 | Métricas (`distance_after == two_opt`, redução) | pytest engine + API | 2-opt ≤ NN; redução e % coerentes | PASSOU | [pytest-optimization.txt](./evidencias/pytest-optimization.txt) |
| S10-OPT-A04 | Persistência em `optimization_runs` | reports + evidence_flow | Histórico / summary após otimização | PASSOU | [evidence-flow.txt](./evidencias/evidence-flow.txt) |
| S10-OPT-A05 | Falha ao gravar não quebra otimização | pytest API (recorder quebrado) | POST ainda retorna 200 | PASSOU | [pytest-optimization.txt](./evidencias/pytest-optimization.txt) |
| S10-OPT-A06 | DDL `optimization_runs` no schema oficial | revisão de arquivos | Tabela em `schema.sql` + Compose `03-` + README DB | PASSOU | `backend/database/schema.sql`, `docker-compose.yml`, `backend/database/README.md` |

## Checklist de prints manuais (PDF / Teams)

Capturar com o sistema no ar (`docker compose up --build`) e salvar em `docs/sprint-10/evidencias/`:

| ID | Captura | Onde |
|---|---|---|
| S10-OPT-01 | Tela `/otimizacao` com rota + métricas | `S10-OPT-01-otimizacao-rota-metricas.png` |
| S10-OPT-02 | Otimização por pedido | `S10-OPT-02-otimizacao-por-pedido.png` |
| S10-OPT-03 | Relatório histórico picking | `S10-OPT-03-relatorio-picking.png` |
| S10-OPT-04 | Swagger `/docs` endpoints `/optimization/*` | `S10-OPT-04-swagger-optimization.png` |
| S10-OPT-05 (opcional) | SQL: `SELECT id, source, distance_before, distance_after, reduction_percent FROM optimization_runs ORDER BY id DESC LIMIT 5` | `S10-OPT-05-optimization-runs-query.png` |

## Suíte automatizada (resumo)

```text
24 passed
```

Arquivo completo: [evidencias/pytest-optimization.txt](./evidencias/pytest-optimization.txt).
