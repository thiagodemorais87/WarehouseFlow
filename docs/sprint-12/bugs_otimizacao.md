# Bugs do módulo de otimização — Sprint 12

**Projeto:** WarehouseFlow — Grupo 26  
**Integrante:** Thiago de Morais Gonçalves  
**Data:** 17/11/2026  
**Branch:** `feature/optimization`

## Smoke realizado

| Verificação | Resultado |
|-------------|-----------|
| Suite pytest motor + providers + coords | **54 passed** |
| `python -m optimization.evidence_flow` | **EVIDÊNCIA OK** (~71% redução, 38 → 11) |
| UI JS (`optimization.js`) usa `/optimization/route` e `/route/by-order` | OK (não chama legado) |
| Persistência oficial `optimization_runs` | OK (best-effort + log em falha) |

Smoke UI via browser/Docker não foi bloqueante: a cobertura automatizada cobre API → motor → reports → CSV.

## Bugs encontrados

Nenhum bug aberto no módulo de otimização após o smoke da Sprint 12.

## Observações (não-bugs)

| Item | Classificação | Ação |
|------|---------------|------|
| Dualidade `optimization_results` vs `optimization_runs` | Dívida documentada | Legado marcado **deprecated**; sem remoção (escopo B) |
| Warnings Starlette/httpx no TestClient | Dependência externa | Fora do escopo do motor |
| Coordenadas derivadas (sem `x,y` nativos no DDL) | Limitação conhecida | Documentada no manual técnico |

## Conclusão

Motor estável e integrado. Nenhum fix de código adicional necessário nesta passagem de Sprint 12.
