# Registro formal de bugs - Sprint 12

**Projeto:** WarehouseFlow - Grupo 26
**Data da validação:** 27/11/2026

| ID | Módulo | Descrição | Reprodução | Esperado | Obtido | Evidência | Prioridade | Status | Correção / justificativa |
|---|---|---|---|---|---|---|---|---|---|
| BUG-001 | API - otimização | `optimization_engine.py` estava truncado no relatório CSV, impedindo a interpretação do módulo e causando 14 erros de coleção. | Executar `python -m pytest -q` ou importar `app.main`. | O módulo deve importar e a aplicação deve iniciar. | `SyntaxError: '[' was never closed` na linha 285. | Saída real do Pytest desta validação. | Crítica | Corrigido | Restaurados os campos finais do CSV e o endpoint `/orders/{order_id}/pick-locations`, com base no conteúdo existente no commit anterior e compatível com a implementação atual de filtros. Compilação e regressão posteriores aprovadas. |
| BUG-002 | Seed / testes | O seed possuía a tabela `optimization_runs`, mas o teste não a incluía no inventário de tabelas. | Executar `python -m pytest -q`. | O teste deve contar todos os blocos `INSERT INTO` idempotentes do seed. | 11 blocos encontrados contra 10 tabelas esperadas pelo teste. | `tests/test_demo_seed.py::test_todo_insert_do_seed_e_idempotente`. | Média | Corrigido | `optimization_runs` foi incluído na lista de tabelas cobertas pelo teste. |
| BUG-003 | Docker Compose | O Compose montava novamente `optimization_runs.sql` embora a tabela já faça parte de `schema.sql`. | Executar inspeção estática do Compose. | Inicialização única com `01-schema.sql` e `02-seed.sql`. | O Compose continha também `03-optimization_runs.sql`. | `tests/test_schema_coerente.py::test_compose_monta_so_o_schema_como_ddl_oficial`. | Média | Corrigido | Removida a montagem duplicada do DDL dedicado. O arquivo continua disponível para bancos legados. |

## Limitações não corrigidas

- A rota por pedido validada com duas posições produziu 14 -> 14 (redução zero). É comportamento válido de heurística, não bug; a rota manual demonstrativa produziu 38 -> 11.
- O PostgreSQL usa um volume preexistente. Os scripts de inicialização não foram reaplicados; nenhum dado/volume foi removido.
- Nenhuma Release ou push remoto foi criado: exigiria publicar no GitHub e alterar o estado remoto, o que não foi autorizado.

As capturas reais de UI e os logs Docker estão em [`evidencias/`](evidencias/).
