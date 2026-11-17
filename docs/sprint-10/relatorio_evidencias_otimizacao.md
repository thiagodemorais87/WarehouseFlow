# Relatório de evidências — Motor de otimização (Sprint 10 RC)

**Projeto:** WarehouseFlow — Grupo 26  
**Integrante:** Thiago de Morais Gonçalves  
**Data:** 10/11/2026  
**Branch:** `feature/optimization-sprint-10`

## Objetivo

Demonstrar, para a Release Candidate, que o motor de otimização:

1. Calcula rota (Nearest Neighbor + 2-opt) com métricas transparentes.
2. Integra API ↔ persistência `optimization_runs` ↔ relatórios.
3. Tem DDL/documentação alinhados ao schema oficial e ao Docker Compose.

## Como reproduzir

### Pré-requisitos

- Python 3.11+ com dependências de `requirements.txt`
- Na raiz do repositório

### Testes automatizados

```powershell
python -m pytest tests/test_api_optimization.py tests/test_optimization_flow_integration.py tests/test_optimization_reports.py tests/test_engine.py -q
```

Resultado observado: **24 passed** — ver [evidencias/pytest-optimization.txt](./evidencias/pytest-optimization.txt).

### Fluxo ponta a ponta (sem UI / sem Postgres compartilhado)

```powershell
$env:PYTHONPATH = "backend"
python -m optimization.evidence_flow
```

Resultado observado: **EVIDÊNCIA OK** — ver [evidencias/evidence-flow.txt](./evidencias/evidence-flow.txt).

Resumo da execução capturada:

| Métrica | Valor |
|---------|-------|
| `distance_before` | 38.0 |
| `distance_after` | 11.0 |
| `distance_reduction` | 27.0 |
| `reduction_percent` | ~71.05% |
| Rota 2-opt | `START > NEAR1 > NEAR2 > FAR1 > FAR2` |
| `runs_count` (summary) | 1 |
| picking + CSV | ok |

### Coerência de `optimization_runs`

| Artefato | Papel |
|----------|--------|
| [backend/database/schema.sql](../../backend/database/schema.sql) | DDL oficial (tabela 11) |
| [backend/database/optimization_runs.sql](../../backend/database/optimization_runs.sql) | Artefato dedicado + init `03` |
| [docker-compose.yml](../../docker-compose.yml) | Monta `03-optimization_runs.sql` |
| [backend/database/README.md](../../backend/database/README.md) | Entidade + dicionário de colunas |
| Model ORM | `backend/app/models/optimization_run.py` |

## Prints manuais (pendentes de captura no ambiente com UI)

Ver checklist em [matriz_otimizacao_sprint10.md](./matriz_otimizacao_sprint10.md):

- S10-OPT-01 … S10-OPT-04 (obrigatórios para o PDF)
- S10-OPT-05 (query SQL opcional)

Comando sugerido para subir o ambiente:

```powershell
docker compose up --build
```

- UI: http://127.0.0.1:8080/otimizacao  
- Swagger: http://127.0.0.1:8000/docs  
- Login seed: `admin@warehouseflow.com` / `admin123`

## Conclusão

A parte automatizada do motor está evidenciada e o schema/doc de `optimization_runs` está alinhado para a RC. Restam apenas as capturas de tela manuais listadas na matriz para anexar ao PDF da Sprint 10.
