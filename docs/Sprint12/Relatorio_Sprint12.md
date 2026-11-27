# Relatório da Sprint 12 - Validação Final

**Projeto:** WarehouseFlow
**Grupo:** 26
**Turma:** 8MB
**Curso:** Ciência da Computação
**Instituição:** UNINASSAU - Centro Universitário Maurício de Nassau - Campus Graças
**Professor:** David Wilber Silva Daltro
**Ano:** 2026

## 1. Identificação da equipe

| Integrante | Matrícula |
|---|---:|
| Gabriel George de Araújo Figueiredo | 01605236 |
| Guilherme Branco Ferrario | 01596391 |
| João Pedro Silva de Araujo | 01606470 |
| Sérgio José de Araújo Júnior | 01590694 |
| Thiago de Morais Gonçalves | 01609695 |

## 2. Escopo executado

Foram inspecionados Git, README, Compose, Docker, código Python, testes, banco e documentação existente. Docker Desktop foi iniciado e os três serviços do Compose foram construídos e executados. Foram verificados fluxos por navegador e por chamadas HTTP à API real conectada ao PostgreSQL.

## 3. Estado inicial

Antes das alterações, o repositório estava limpo no branch `main`, sincronizado com `origin/main`. A execução inicial da suíte não conseguiu iniciar a coleta porque `backend/app/routers/optimization_engine.py` terminava no meio do endpoint CSV, em uma lista Python aberta.

Docker Desktop 4.92.0 / Engine 29.8.0 foi iniciado com sucesso. `docker compose up --build -d` iniciou PostgreSQL 16 healthy em `localhost:5433`, API FastAPI em `http://127.0.0.1:8000` e frontend Nginx em `http://127.0.0.1:8080`. `/health` retornou `{"status":"ok","version":"dev"}`; Swagger e login responderam HTTP 200.

O volume PostgreSQL preexistente foi preservado; os logs informaram que a base já continha dados e não repetiram os scripts de inicialização. Nenhum volume/dado preexistente foi apagado.

## 4. Correções realizadas

- Restaurada a implementação final do relatório CSV e do endpoint de posições de picking no arquivo do motor.
- Atualizada a cobertura do seed para incluir `optimization_runs`.
- Removida a montagem duplicada de `optimization_runs.sql` no Compose, pois o DDL já está em `schema.sql`.

## 5. Testes

| Validação | Resultado |
|---|---|
| `python -m compileall -q backend tests` | Aprovado após a correção. |
| `python -m pytest -q` | 239 passed, 66 skipped, 1 warning. |
| Smoke API/motor | EVIDÊNCIA OK. |
| `docker compose config --quiet` | Configuração válida. |
| `docker compose up --build -d` | Concluído; db healthy, API e frontend ativos. |
| Navegador | Login, dashboard e 10 páginas principais responderam HTTP 200 como ADMIN. |

### Fluxos executados na stack Docker

| Módulo/fluxo | Resultado observado |
|---|---|
| Login | Login web/API como ADMIN aprovado; credencial inválida retornou 401. Logout web retornou à tela de login. |
| Usuários e permissões | Criar usuário OPERADOR, consultar, filtrar, autenticar, editar e apagar; após apagar, GET retornou 404. Usuário OPERADOR recebeu 403 ao criar outro usuário. A listagem somente leitura `GET /users/` retorna 200 a perfis autenticados conforme matriz; a tela `/usuarios` negou acesso ao operador com 403. |
| Produtos | Criar, listar/buscar, consultar, editar e apagar dados de teste; SKU duplicado retornou 409 e campos vazios retornaram 400. |
| Posições/armazém | Criar e consultar armazém/posições; editar posição e limpar os dados de teste. |
| Estoque | Criar, filtrar, editar, entrada e saída aprovados; saída acima do saldo retornou 409. |
| Pedidos | Criar OUTBOUND, listar/filtrar, atualizar status, adicionar/editar item; quantidade zero retornou 400. |
| Tarefas | Criar PICKING, consultar, atualizar para IN_PROGRESS e COMPLETED; exclusão de teste aprovada. |
| Relatórios | Dashboard, relatório de pedidos, movimentações de estoque e picking responderam 200. Exportações `orders.csv`, `stock-movements.csv` e `picking.csv` responderam 200 e continham dados/cabeçalho. |
| Otimização manual | NN + 2-opt: 38 → 11; redução 27 (71,0526%); `execution_time_ms`: 0,0278 ms na API e 0,02 ms na UI. |
| Otimização por pedido | POST real retornou 200; distância 14 → 14, redução 0%. Resultado válido para esta entrada, sem melhoria. |
| Entradas inválidas | IDs de rota duplicados retornaram 400; SKU duplicado 409; saída insuficiente 409. |

Os registros temporários criados para CRUD e o usuário descartável foram removidos ao fim do fluxo. A validação de usuário comprovou login após criação, edição, exclusão e resposta 404 após remoção. A execução manual de rota foi mantida no histórico para refletir execuções reais demonstráveis.

O primeiro teste do filtro de usuários usou `role=OPERATOR`, valor não aceito pelo contrato (`ADMIN`, `GESTOR`, `OPERADOR`), e recebeu 400. O teste foi repetido com `role=OPERADOR` e retornou 200; não é bug da aplicação.

### Capturas reais do sistema

As capturas de tela foram feitas no navegador integrado contra o frontend servido pelo container Nginx e estão em [`evidencias/`](evidencias/). Incluem login, dashboard, produtos, estoque, posições, pedidos, tarefas, otimização com resultado, relatórios, usuários, permissão de operador, logout e Swagger.

Resultados detalhados das chamadas reais: [`docker-fluxos-principais.txt`](evidencias/docker-fluxos-principais.txt) e [`docker-usuarios-relatorios.txt`](evidencias/docker-usuarios-relatorios.txt).

PDF exclusivo: [`Grupo26_WarehouseFlow_Sprint12.pdf`](Grupo26_WarehouseFlow_Sprint12.pdf).  
PDF acumulado das Sprints 1 a 12: [`Relatorio_Final_Sprints_1_a_12.pdf`](Relatorio_Final_Sprints_1_a_12.pdf); cópia de entrega em [`docs/entrega-final/Grupo26_WarehouseFlow_Sprints_1_a_12.pdf`](../entrega-final/Grupo26_WarehouseFlow_Sprints_1_a_12.pdf).

### Smoke do motor

- `distance_before`: 38
- `distance_after`: 11
- `distance_reduction`: 27
- `reduction_percent`: 71.05263157894737
- Rota 2-opt: `START > NEAR1 > NEAR2 > FAR1 > FAR2`
- Summary: 1 execução
- CSV: 2 linhas, incluindo cabeçalho

## 6. Bugs

Três ocorrências foram formalizadas em [`Registro_Bugs_Sprint12.md`](Registro_Bugs_Sprint12.md):

1. arquivo de otimização truncado: corrigido;
2. teste do seed sem `optimization_runs`: corrigido;
3. montagem duplicada de DDL no Compose: corrigida.

## 7. Code Freeze e Release

Não foi declarada versão/tag final nesta execução. A validação Docker foi concluída, mas as alterações e os relatórios ainda estão no worktree local, sem commit/tag final e sem ensaio/aprovação da equipe. Nenhuma Release nem push remoto foi criado.

## 8. Evidências

Os resultados automatizados, logs Compose, smoke e capturas reais do navegador foram registrados em [`evidencias/`](evidencias/).

## 9. Tarefas pendentes

- Executar ensaio geral.
- Gravar o vídeo demonstrativo.
- Aprovar o commit/tag de versão final e criar Release somente após revisão da equipe.
