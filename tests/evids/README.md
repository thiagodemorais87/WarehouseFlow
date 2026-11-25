# Evidencias dos testes de interface

**Data:** 23/10/2026  
**Ambiente:** front-end `http://127.0.0.1:8080`, API `http://127.0.0.1:8000`, PostgreSQL via Docker Compose.  
**Conta de acesso:** `admin@warehouseflow.com` (senha de demonstração já documentada no README do projeto).

Os fluxos visuais foram executados no navegador integrado. As verificações de perfis e busca foram complementadas com chamadas autenticadas à API, pois a interface não possui uma tela de administração de usuários. As capturas PNG abaixo registram as telas e os resultados observados.

## Resultado por cenário

| Cenário solicitado | Resultado | Evidência / observação |
|---|---|---|
| Dashboard carregando os indicadores | **PASSOU** | [01-dashboard-indicadores.png](./01-dashboard-indicadores.png) — indicadores carregados: 4 produtos, 155 unidades, 1 pedido pendente e 0 tarefas em andamento. |
| Relatório de picking completo | **FALHOU / não implementado na interface** | [03-relatorio-picking-nao-encontrado.png](./03-relatorio-picking-nao-encontrado.png) — `/relatorios/picking` responde HTTP 404. A tela de otimização calcula e apresenta métricas de uma rota, mas não é um relatório completo de picking. |
| Pesquisa de usuário por e-mail existente e inexistente | **FALHOU / não implementado** | [04-usuarios-sem-tela-de-pesquisa.png](./04-usuarios-sem-tela-de-pesquisa.png) e [08-resultados-rbac-e-busca.png](./08-resultados-rbac-e-busca.png) — “Usuários” aponta para `#`, sem abrir uma tela. A API também ignorou o parâmetro `email`: as buscas por e-mail existente e inexistente retornaram 8 usuários cada. |
| Filtro funcionando | **PASSOU** | [02-filtro-pedidos-recebimento.png](./02-filtro-pedidos-recebimento.png) — ao selecionar “Recebimento”, a tabela exibiu somente o pedido de entrada. |
| Exportação CSV abrindo corretamente | **FALHOU / não implementado** | [05-pedidos-sem-exportacao-csv.png](./05-pedidos-sem-exportacao-csv.png) — não há botão/controle de CSV na tela de pedidos. |
| Histórico de login com sucesso e falha | **PARCIAL** | Login válido abriu o dashboard ([01-dashboard-indicadores.png](./01-dashboard-indicadores.png)); senha inválida mostrou “E-mail ou senha incorretos” ([06-login-falha-sem-historico.png](./06-login-falha-sem-historico.png)). Não foi encontrada tela, rota ou armazenamento de histórico de tentativas. |
| Histórico de alteração de usuário e otimização | **PARCIAL / não disponível na interface** | Não foi encontrado histórico/auditoria de alterações de usuários. A API possui `/optimization-results/` e havia um resultado salvo, mas a interface não exibe um histórico; a otimização executada na tela retorna o resultado sem adicioná-lo a esse histórico. [07-otimizacao-de-picking.png](./07-otimizacao-de-picking.png) e [08-resultados-rbac-e-busca.png](./08-resultados-rbac-e-busca.png). |
| Permissões de ADMIN, GESTOR e OPERADOR | **PARCIAL — falha de autorização para OPERADOR** | [08-resultados-rbac-e-busca.png](./08-resultados-rbac-e-busca.png) — criar usuário: ADMIN HTTP 201; GESTOR e OPERADOR HTTP 403. Porém, o OPERADOR recebeu tarefas de outros usuários, consultou uma tarefa alheia e alterou o responsável (HTTP 200 nos três casos; esperado filtro/HTTP 403). |

## Detalhes e limitações observadas

- Os filtros de tipo de pedido funcionam na interface. A busca por e-mail não existe: não há tela de usuários, e a API não aplica `email` como filtro.
- A interface oferece cálculo manual de rota e exibe distância, redução e etapas do algoritmo; isso não equivale a um relatório completo de picking vinculado a um pedido.
- A API permite listar resultados de otimização já salvos, mas não há uma tela para consultar esse histórico. A execução de otimização testada não salvou um novo resultado.
- A falha de permissão do OPERADOR deve ser corrigida antes de considerar esse perfil validado. Com os nomes de perfil atualmente usados pelo banco, as restrições de leitura e alteração de tarefas não foram aplicadas.
- Mesmo após o login como ADMIN, o cabeçalho mostra o usuário estático “Usuário Teste”; a interface não reflete a identidade/perfil autenticado.
- Contas e tarefa temporárias criadas para validar as permissões foram removidas ao final. A conferência posterior encontrou zero usuários de QA e uma tarefa de demonstração preexistente.
