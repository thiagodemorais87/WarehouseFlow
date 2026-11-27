# Checklist do ensaio geral - Sprint 12

| Item | Responsável | Status | Observações |
|---|---|---|---|
| Computadores preparados | Equipe | Pendente | Validar antes do ensaio presencial. |
| VS Code disponível | Equipe | Pendente | Confirmar acesso ao projeto e terminal. |
| Docker Desktop iniciado | Equipe | Pendente | Nesta validação o daemon estava indisponível. |
| Containers iniciados | Equipe | Pendente | Executar `docker compose up --build`. |
| API disponível | Equipe | Pendente manual | Validar `GET /health` e `/docs`. |
| Frontend disponível | Equipe | Pendente manual | Validar `http://127.0.0.1:8080`. |
| PostgreSQL conectado | Equipe | Pendente manual | Validar container e usuários do seed. |
| Dependências instaladas | Equipe | Pendente | Validar ambiente Python e requisitos. |
| `.env` configurado | Equipe | Pendente | Não versionar secrets reais. |
| Internet disponível | Equipe | Pendente | Necessária apenas para recurso externo, se utilizado. |
| Plano de contingência preparado | Equipe | Pendente | Preparar execução via testes locais/TestClient. |
| Banco inicializado | Equipe | Pendente manual | Schema e seed aplicados na primeira inicialização. |
| Tabelas verificadas | Equipe | Pendente manual | Validar relacionamentos no PostgreSQL. |
| Dados de demonstração disponíveis | Equipe | Pendente manual | Seed contém usuários, produtos, pedidos e tarefas. |
| Usuários de teste preparados | Equipe | Pendente manual | Login de admin registrado no README. |
| Login | Equipe | Pendente manual | Capturar credenciais válidas e inválidas. |
| Usuários e permissões | Equipe | Pendente manual | Validar ADMIN, OPERADOR e GESTOR. |
| Produtos | Equipe | Pendente manual | Cadastro, consulta, edição e exclusão. |
| Estoque | Equipe | Pendente manual | Entradas, saídas e baixa de estoque. |
| Pedidos | Equipe | Pendente manual | Criação, consulta e status. |
| Tarefas | Equipe | Pendente manual | Criação, atribuição e atualização de status. |
| Relatórios | Equipe | Pendente manual | Picking e movimentações, incluindo CSV. |
| Otimização | Equipe | Pendente manual | Validar NN, 2-opt e métricas. |
| Swagger/API | Equipe | Pendente manual | Validar `/docs` e `/openapi.json`. |
| Cenário NN/2-opt preparado | Equipe | Pendente manual | Usar cenário real já validado: 38 -> 11. |
| Entrada da rota definida | Equipe | Pendente manual | Definir lista antes da demonstração. |
| Resultado esperado registrado | Equipe | Pendente manual | Aguardar confirmação visual em execução real. |
| Integrantes identificados | Equipe | Pendente | Usar nomes e matrículas deste documento. |
| Falas distribuídas | Equipe | Pendente | Seguir o roteiro de 8 minutos. |
| Ordem definida | Equipe | Pendente | Cenas 1 a 10 do roteiro. |
| Transições ensaiadas | Equipe | Pendente | Evitar troca longa entre módulos. |
| Tempo cronometrado | Equipe | Pendente | Alvo: 8 minutos. |
| Perguntas possíveis levantadas | Equipe | Pendente | Preparar respostas sobre algoritmo, RBAC e Docker. |
| Contingência definida | Equipe | Pendente | Usar Pytest/evidência automatizada caso Docker falhe. |
