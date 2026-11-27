# Checklist de evidências - Sprint 12

| Evidência | Arquivo / referência | Status | Observação |
|---|---|---|---|
| Código compilado | Saída do `compileall` | Capturada no registro de execução | Sem erros após a correção. |
| Suíte Pytest completa | [`docs/Sprint12/evidencias/pytest-results.txt`](evidencias/pytest-results.txt) | Capturada | 239 passed, 66 skipped, 1 warning. |
| Smoke da API/motor | [`docs/Sprint12/evidencias/evidence-flow.txt`](evidencias/evidence-flow.txt) | Capturada | NN/2-opt, 38 -> 11, redução de 71,0526%. |
| Docker engine/containers | [`docker-compose-ps.txt`](evidencias/docker-compose-ps.txt) e [`docker-compose-logs.txt`](evidencias/docker-compose-logs.txt) | Capturada | `db` healthy; API e frontend ativos. |
| Docker Compose estático | `docker compose config --quiet` | Aprovado | Configuração válida. |
| Git limpo antes da validação | Saída `git status --short --branch` | Capturada | `main`, sincronizado com `origin/main`, sem alterações locais antes do trabalho. |
| Login | [`EV-01-login.png`](evidencias/EV-01-login.png) | Capturada | Tela real antes de autenticar. |
| Login com credencial inválida | [`EV-15-login-credenciais-invalidas.png`](evidencias/EV-15-login-credenciais-invalidas.png) | Capturada | UI exibiu “E-mail ou senha incorretos”. |
| Dashboard | `EV-dashboard.png` | Capturada | Tela real servida pelo Docker. |
| Produtos, estoque, posições, pedidos e tarefas | `EV-products.png`, `EV-stock.png`, `EV-locations.png`, `EV-orders.png`, `EV-tasks.png` | Capturadas | Páginas reais respondendo HTTP 200. |
| Otimização com resultado | [`EV-11-resultado-otimizacao.png`](evidencias/EV-11-resultado-otimizacao.png) | Capturada | 38 → 11; NN e 2-opt exibidos na tela. |
| Relatórios | `EV-picking-report-final.png`, `EV-13-stock-movements-report-admin.png` | Capturados | Relatórios reais autenticados como ADMIN. |
| Usuários e permissão | `EV-users.png`, `EV-12-operador-acesso-usuarios.png` | Capturados | Admin acessa; operador recebe 403 na página `/usuarios`. |
| CRUD de usuários e permissões API | [`docker-usuarios-relatorios.txt`](evidencias/docker-usuarios-relatorios.txt) | Capturado | Criar, consultar, filtrar, autenticar, editar, excluir e confirmar 404. |
| Exportações CSV | [`docker-usuarios-relatorios.txt`](evidencias/docker-usuarios-relatorios.txt) | Capturadas | Relatórios de pedidos, movimentação de estoque e picking. |
| Logout | [`EV-14-logout.png`](evidencias/EV-14-logout.png) | Capturada | Retorno à tela de login. |
| Swagger/OpenAPI | [`EV-16-swagger-api.png`](evidencias/EV-16-swagger-api.png) | Capturada | Swagger UI real; `/docs` respondeu HTTP 200. |
| Tag/Release | Não criada | Pendente | Criar localmente/remotamente somente após decisão da equipe. |
