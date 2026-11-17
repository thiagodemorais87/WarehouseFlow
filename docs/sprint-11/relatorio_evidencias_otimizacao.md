# Relatório de evidências — Motor de otimização (Sprint 11)

**Projeto:** WarehouseFlow — Grupo 26  
**Integrante:** Thiago de Morais Gonçalves  
**Data:** 17/11/2026  
**Branch:** `feature/optimization`

## Objetivo

Demonstrar, na preparação para entrega (Sprint 11), que o motor:

1. Calcula rota (Nearest Neighbor + 2-opt) com métricas transparentes.
2. Integra API ↔ persistência oficial `optimization_runs` ↔ relatórios.
3. Tem documentação alinhada (oficial vs legado deprecated) e limpeza média do módulo.
4. Possui manual técnico com seção do componente de otimização.

## Limpeza média (escopo B) nesta sprint

| Item | Status |
|------|--------|
| `/optimization-results` marcado **deprecated** | OK |
| Logging em falha de `OptimizationRunRecorder` | OK |
| Docs: `optimization_runs` oficial vs `optimization_results` legado | OK |
| `docs/optimization.md` sem texto stale sobre `order_id` futuro | OK |
| `docs/manual-tecnico.md` (seção motor) | OK |
| Tabelas/rotas legadas **não** removidas | OK (proposital) |

## Como reproduzir

### Pré-requisitos

- Python 3.11+ com dependências de `requirements.txt`
- Na raiz do repositório

### Testes automatizados

```powershell
python -m pytest tests/test_api_optimization.py tests/test_optimization_flow_integration.py tests/test_optimization_reports.py tests/test_engine.py tests/test_distance.py tests/test_nearest_neighbor.py tests/test_two_opt.py -q
```

Resultado observado: **39 passed** — ver [evidencias/pytest-optimization.txt](./evidencias/pytest-optimization.txt).

### Fluxo ponta a ponta (sem UI / sem Postgres compartilhado)

```powershell
$env:PYTHONPATH = "backend"
python -m optimization.evidence_flow
```

Resultado observado: **EVIDÊNCIA OK** — ver [evidencias/evidence-flow.txt](./evidencias/evidence-flow.txt).

| Métrica | Valor |
|---------|-------|
| `distance_before` | 38.0 |
| `distance_after` | 11.0 |
| `distance_reduction` | 27.0 |
| `reduction_percent` | ~71.05% |
| Rota 2-opt | `START > NEAR1 > NEAR2 > FAR1 > FAR2` |
| `runs_count` (summary) | 1 |
| picking + CSV | ok |

### Persistência oficial vs legado

| Artefato | Papel |
|----------|--------|
| `optimization_runs` + `/optimization/*` | **Oficial** — motor NN + 2-opt |
| `optimization_results` + `/optimization-results` | **Legado (deprecated)** — CRUD por tarefa |
| [docs/manual-tecnico.md](../manual-tecnico.md) | Manual técnico — seção do motor |
| [docs/optimization.md](../optimization.md) | Detalhe profundo |

## Checklist de prints UI (para o PDF)

Capturar com o ambiente Compose quando disponível:

```powershell
docker compose up --build
```

- UI: http://127.0.0.1:8080/otimizacao  
- Swagger: http://127.0.0.1:8000/docs  
- Login seed: `admin@warehouseflow.com` / `admin123`

| ID | Evidência | Arquivo sugerido |
|----|-----------|------------------|
| S11-OPT-01 | Tela `/otimizacao` (modo manual ou por pedido) | `evidencias/S11-OPT-01-otimizacao.png` |
| S11-OPT-02 | Métricas exibidas (before/after, %, tempo) | `evidencias/S11-OPT-02-metricas.png` |
| S11-OPT-03 | Relatório picking / histórico | `evidencias/S11-OPT-03-relatorio-picking.png` |

> Prints manuais dependem do Docker/UI no ambiente local; as evidências automatizadas acima já comprovam o motor.

## Conclusão

O motor permanece estável (39 pytest + evidence_flow OK), com documentação e histórico oficial alinhados para a entrega. Próximo passo (Sprint 12): smoke integrado, bugs residuais e roteiro de demo do diferencial.
