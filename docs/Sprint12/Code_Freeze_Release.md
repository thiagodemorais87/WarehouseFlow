# Code Freeze e Release - Sprint 12

## Situação

**Code Freeze:** não declarado.
**Motivo:** a validação Docker/PostgreSQL foi concluída, mas os novos documentos e correções ainda não foram commitados nem aprovados para uma versão final pela equipe.

## Registro da validação

| Item | Resultado |
|---|---|
| Estado inicial do Git | Limpo; branch `main` sincronizado com `origin/main`. |
| Versão/tag existente | Tags existentes: `1.0.0`, `2.0.0` e `v2.0.0-rc.1`. |
| Correções desta Sprint | Arquivo de otimização restaurado; Compose sem DDL duplicado; teste de seed atualizado. |
| Pytest | 239 passed, 66 skipped, 1 warning. |
| Docker Compose estático | Configuração válida. |
| Docker daemon | Disponível; PostgreSQL healthy, API e Nginx ativos. |
| Fluxos principais em Docker | Executados; evidência em `evidencias/docker-fluxos-principais.txt`. |
| Tag final criada | Não criada. |
| Release criada | Não criada. |
| Push remoto | Não realizado. |

## Condições para concluir

1. Revisar evidências e relatórios com a equipe.
2. Ensaiar a demonstração e aprovar a versão/tag final.
3. Criar commit/tag e Release somente após aprovação, sem publicar remotos sem autorização.

## Dados provisórios

- **Versão candidata:** `v2.0.0`
- **Tag candidata:** `v2.0.0`
- **Política:** não usar candidato automaticamente como tag final sem validação Docker/PostgreSQL.
