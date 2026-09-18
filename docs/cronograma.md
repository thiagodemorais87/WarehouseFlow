# WarehouseFlow — Cronograma oficial (Fábrica de Software)

Calendário alinhado às **tarefas oficiais do Teams** (prazos da professora).  
Use este arquivo ao montar o **PDF acumulado** de cada sprint (Sprints anteriores + atual).

> Proposta: [proposta.md](proposta.md) · Motor: [optimization.md](optimization.md) · PDF Sprint 01: [Sprint01_WarehouseFlow_8MB.pdf](Sprint01_WarehouseFlow_8MB.pdf)

**Turma:** 8MA — Manhã · **Projeto:** WarehouseFlow  
**Entrega no Teams:** 1 PDF por sprint, identificado com **número do grupo + nome do projeto**, enviado pelo **Scrum Master**.

---

## Visão geral (datas-limite oficiais)

| Sprint | Título (Teams) | Prazo final | Foco WarehouseFlow | Status |
|--------|----------------|-------------|--------------------|--------|
| 01 | Planejamento do projeto | **05/09/2026** 23:59 | Documento de planejamento + GitHub + Forms | Concluída |
| 02 | Arquitetura e modelagem | **19/09/2026** 23:59 | Arquitetura, diagramas, MER, protótipo, DB criado | Em andamento |
| 03 | Estrutura inicial funcionando | **19/09/2026** 23:59 | DB conectado, auth, CRUD, deploy local | Em andamento |
| 04 | Primeiro módulo completo | **26/09/2026** 23:59 | Módulo **Produtos e Estoque** (fluxo completo + telas) | Planejada |
| 05 | Segundo módulo funcionando | **03/10/2026** 23:59 | Módulo **Pedidos e Tarefas** | Planejada |
| 06 | Aprimoramento do sistema | **17/10/2026** 23:59 | Módulo **Otimização de picking** + correções Pré-Banca | Planejada |
| 07 | Sistema quase completo | **24/10/2026** 23:59 | Dashboard, relatórios, pesquisa, filtros, logs | Planejada |
| 08 | Sistema praticamente concluído | **31/10/2026** 23:59 | Funcionalidades fechadas + permissões + usabilidade | Planejada |
| 09 | Testes completos | **07/11/2026** 23:59 | Testes funcionais, validação, navegação, docs | Planejada |
| 10 | Versão Release Candidate | **14/11/2026** 23:59 | Sistema estável, interface/DB finais, APIs, README | Planejada |
| 11 | Preparação para entrega | **21/11/2026** 23:59 | Manual do usuário, manual técnico, code review | Planejada |
| 12 | Versão final do sistema | **28/11/2026** 23:59 | Code freeze, bugs, ensaio, vídeos | Planejada |
| — | **Entrega final** | **05/12/2026** 23:59 | Sistema + docs + vídeos YouTube/Instagram | Planejada |

> Sprint 02 teve prazo original 12/09; a professora **alterou para 19/09**. Sprint 02 e 03 compartilham a mesma data-limite.

---

## Mapa dos módulos do WarehouseFlow

Para o relatório, trate estes **3 módulos principais** (além de auth e indicadores):

| Módulo | Conteúdo | Sprint de consolidação |
|--------|----------|------------------------|
| **1 — Produtos e Estoque** | Produtos, posições/armazém, saldo de estoque | Sprint 04 |
| **2 — Pedidos e Tarefas** | Pedidos INBOUND/OUTBOUND, itens, tarefas PICKING/PUTAWAY | Sprint 05 |
| **3 — Otimização de picking** | Motor NN + 2-opt, métricas, rota sugerida ligada a pedidos | Sprint 06 |

**Perfis previstos:** `ADMIN` · `GESTOR` · `OPERADOR`

---

## Sprint 01 — Planejamento do projeto

**Prazo:** 05/09/2026 · **Status:** Concluída

### Entregas obrigatórias (Teams)

* Identificação da equipe (nomes, turma, projeto)
* Escolha do tema / contexto
* Definição do problema e relevância
* Objetivos (geral + resultados esperados)
* Público-alvo
* Requisitos funcionais e não funcionais
* Casos de uso iniciais
* Product Backlog
* Cronograma inicial
* Link do repositório GitHub
* **Também:** preencher Forms `https://forms.gle/o1sAEPZz7eSvTq1v7` (ação separada do PDF)

### Funcionalidades / itens previstos nesta sprint (planejamento)

*Não há código obrigatório.* Registrar no backlog o que será desenvolvido depois:

* RF: cadastro de produtos, estoque, posições, pedidos, tarefas, usuários
* RF: login e perfis (ADMIN / GESTOR / OPERADOR)
* RF: otimização de rota de picking com métricas (diferencial)
* RF: indicadores / dashboard (sprints finais)
* RNF: PostgreSQL, FastAPI, deploy local, segurança de senhas, usabilidade

### Evidências no repo

* [Sprint01_WarehouseFlow_8MB.pdf](Sprint01_WarehouseFlow_8MB.pdf)
* [proposta.md](proposta.md) (versão atualizada pós-feedback)

### Para o PDF do relatório

Incluir equipe completa (com Guilherme Branco Ferrario — 01596391), link GitHub, e notar que o diferencial computacional (otimização) foi reforçado após feedback da professora.

---

## Sprint 02 — Arquitetura e modelagem do sistema

**Prazo:** 19/09/2026 · **Status:** Em andamento

### Entregas obrigatórias (Teams)

1. Arquitetura do sistema (componentes + integração com o componente avançado)
2. Diagrama de classes
3. Modelo Entidade-Relacionamento (MER)
4. Modelo relacional (tabelas, PK, FK)
5. Protótipo das telas principais (Figma)
6. Banco de dados criado (estrutura inicial)
7. Projeto estruturado no GitHub

### Funcionalidades / artefatos a documentar (WarehouseFlow)

| Item | Conteúdo concreto do projeto |
|------|------------------------------|
| Arquitetura | Front (Jinja/HTML) → FastAPI → PostgreSQL + pacote `backend/optimization/` |
| Classes | User, Role, Product, Warehouse, Location, Stock, Order, OrderItem, Task, OptimizationResult |
| MER / Relacional | `roles`, `users`, `products`, `warehouses`, `locations`, `stock`, `orders`, `order_items`, `tasks`, `optimization_results` |
| Protótipo | Figma (link no README) — login e telas principais |
| Banco criado | `backend/database/schema.sql` + `seed.sql` + Docker Postgres |
| Componente avançado | Motor NN + 2-opt (documentar na arquitetura mesmo se a UI ainda for parcial) |

### Evidências no repo

* `backend/database/README.md`, `schema.sql`, `seed.sql`
* `docker-compose.yml` (serviço `db`)
* `docs/optimization.md`
* Link Figma no README

### Para o PDF do relatório

PDF acumulado: **Sprint 01 + Sprint 02**. Explicar cada diagrama; não entregar só imagens soltas. Justificar continuidade com o problema da Sprint 01 (picking / deslocamento).

---

## Sprint 03 — Estrutura inicial funcionando

**Prazo:** 19/09/2026 · **Status:** Em andamento

### Entregas obrigatórias (Teams)

1. Banco de dados conectado
2. Login funcional (credenciais no banco)
3. Cadastro de usuários
4. Controle inicial de perfis
5. CRUD principal funcionando (persistência real)
6. Primeiro deploy local + instruções

### Funcionalidades a desenvolver / demonstrar

| # | Funcionalidade | Endpoints / como mostrar | Responsável sugerido |
|---|----------------|--------------------------|----------------------|
| 1 | Conexão PostgreSQL | `DATABASE_URL`, `create_all` / SQLAlchemy | Backend/DB |
| 2 | Login | `POST /auth/login` (JWT) + tela `/login` | Auth (Pessoa 2) |
| 3 | Cadastro de usuários | `POST /users`, `GET /users`, etc. | Auth |
| 4 | Perfis | Roles ADMIN/GESTOR/OPERADOR + bloqueio de rotas | Auth |
| 5 | CRUD principal (**Produtos**) | `POST/GET/PUT/DELETE /products` | Backend |
| 6 | Deploy local | `docker compose up --build` + README | Todos |

### Já existente no repo (aproveitar no relatório)

* DB conectado + CRUD `/products`, `/stock`, `/orders`, `/tasks`, `/locations`, `/users`
* Deploy: Compose API + Postgres
* **Pendente crítico Sprint 03:** login JWT real, hash bcrypt, enforcement de perfis (branch `feature/auth-users`)

### Para o PDF do relatório

Incluir: descrição da estrutura; prints/evidências de DB, login, cadastro, perfis, CRUD; passo a passo local; link GitHub; dificuldades e próximos passos.

---

## Sprint 04 — Primeiro módulo completo

**Prazo:** 26/09/2026 · **Status:** Planejada

### Entregas obrigatórias (Teams)

1. Primeiro módulo totalmente funcional (fluxo completo)
2. Persistência de dados
3. Validações
4. Mensagens de erro
5. Navegação entre telas
6. Commits organizados

### Módulo 1 — Produtos e Estoque (funcionalidades)

| Funcionalidade | Detalhe |
|----------------|---------|
| Cadastro de produtos | SKU, nome, descrição, peso, volume |
| Listagem / busca de produtos | Filtro por SKU ou nome |
| Edição e exclusão de produtos | Validações (SKU único, campos obrigatórios) |
| Cadastro de armazém e posições | Código, corredor, estante, prateleira |
| Controle de estoque | Quantidade por produto × posição |
| Entrada/ajuste de saldo | Atualização persistida |
| Telas HTML | Listar / criar / editar produtos e estoque |
| Navegação | Menu entre Login → Produtos → Estoque → Posições |
| Mensagens | Erro de SKU duplicado, campo vazio, estoque inválido |

### Para o PDF do relatório

Evidências do fluxo completo na UI (não só Swagger), persistência após restart, exemplos de validação e mensagem de erro, commits claros.

---

## Sprint 05 — Segundo módulo funcionando

**Prazo:** 03/10/2026 · **Status:** Planejada

### Entregas obrigatórias (Teams)

1. Segundo módulo completo
2. Integração com banco
3. Atualização das regras de negócio
4. Testes das funcionalidades
5. Correção dos bugs encontrados

### Módulo 2 — Pedidos e Tarefas (funcionalidades)

| Funcionalidade | Detalhe |
|----------------|---------|
| Criar pedido | Tipo INBOUND / OUTBOUND + itens (produto + quantidade) |
| Consultar / atualizar status | PENDING → PROCESSING → COMPLETED / CANCELLED |
| Itens do pedido | Persistência em `order_items` |
| Criar tarefas | PICKING, PUTAWAY, REPLENISHMENT vinculadas ao pedido |
| Atribuir operador | `assigned_user_id` |
| Atualizar status da tarefa | PENDING → IN_PROGRESS → COMPLETED |
| Regras de negócio | Pedido precisa de ≥1 item; tarefa referencia pedido válido |
| Telas | Pedidos, detalhe do pedido, lista de tarefas |
| Testes | Fluxos felizes + erros (produto inexistente, qtd ≤ 0) |
| Bugs | Registrar achados e correções no PDF |

### Para o PDF do relatório

Descrição do módulo 2, evidências UI + DB, regras alteradas vs Sprint 01, tabela de testes, bugs/correções.

---

## Sprint 06 — Aprimoramento do sistema

**Prazo:** 17/10/2026 · **Status:** Planejada

### Entregas obrigatórias (Teams)

1. Correções da Pré-Banca
2. Terceiro módulo implementado
3. Integração entre módulos
4. Melhorias na interface
5. Ajustes de navegação

### Módulo 3 — Otimização de picking (funcionalidades)

| Funcionalidade | Detalhe |
|----------------|---------|
| Otimizar rota (API) | `POST /optimization/route` (já existe) |
| Otimizar a partir de pedido | `order_id` → posições (x,y) → motor |
| Exibir rotas | Original, NN, 2-opt |
| Exibir métricas | Distâncias, redução %, `execution_time_ms` |
| Salvar resultado | `optimization_results` ligado à tarefa |
| Integração | Pedido (M2) → posições/estoque (M1) → motor (M3) |
| UI | Tela “Otimizar picking” com resultado legível |
| Pré-Banca | Checklist de observações + ações no PDF |

### Para o PDF do relatório

Registro Pré-Banca → ações; evidências do módulo 3; fluxos integrados M1+M2+M3; antes/depois da UI e navegação.

---

## Sprint 07 — Sistema quase completo

**Prazo:** 24/10/2026 · **Status:** Planejada

### Entregas obrigatórias (Teams)

1. Dashboard
2. Relatórios
3. Pesquisas
4. Filtros
5. Exportação (ou justificativa se N/A)
6. Logs / histórico de operações

### Funcionalidades a desenvolver

| Funcionalidade | Detalhe WarehouseFlow |
|----------------|----------------------|
| Dashboard | Indicadores: pedidos pendentes, tarefas abertas, estoque baixo, **redução média de distância** das otimizações |
| Relatórios | Relatório de picking (rotas/métricas); relatório de movimentação de estoque |
| Pesquisa | Busca de produtos (SKU/nome), pedidos por status, usuários por e-mail |
| Filtros | Período, status do pedido/tarefa, tipo INBOUND/OUTBOUND, perfil |
| Exportação | CSV (ou PDF) de relatório de otimização / pedidos — se não houver, justificar |
| Logs | Histórico: login, CRUD crítico, execução de otimização (quem/quando/resultado) |

---

## Sprint 08 — Sistema praticamente concluído

**Prazo:** 31/10/2026 · **Status:** Planejada

### Entregas obrigatórias (Teams)

1. Todas as funcionalidades previstas implementadas
2. Controle de permissões
3. Melhorias de usabilidade
4. Revisão geral das regras de negócio

### Funcionalidades / fechamentos

| Item | Detalhe |
|------|---------|
| Escopo fechado | M1 + M2 + M3 + dashboard/relatórios da S07 |
| Permissões | ADMIN: tudo · GESTOR: estoque, indicadores, otimização · OPERADOR: estoque, pedidos, tarefas |
| Usabilidade | Labels claros, feedback visual, fluxos curtos |
| Regras | Revisar status de pedido/tarefa, estoque negativo, exclusões com dependência |
| Escopo alterado | Qualquer RF cortado deve ser justificado no PDF |

---

## Sprint 09 — Testes completos

**Prazo:** 07/11/2026 · **Status:** Planejada

### Entregas obrigatórias (Teams)

1. Testes funcionais
2. Correção de bugs
3. Testes de validação
4. Testes de navegação
5. Atualização da documentação

### O que registrar no relatório

| Tipo | Exemplos no WarehouseFlow |
|------|---------------------------|
| Funcionais | Login, CRUD produtos, criar pedido → tarefa → otimizar rota |
| Validação | SKU vazio, senha curta, quantidade ≤ 0, e-mail duplicado |
| Navegação | Menus, redirect pós-login, bloqueio por perfil |
| Automatizados | Manter/expandir `pytest` do motor + testes de API |
| Docs | Atualizar proposta, cronograma, README, database README |

---

## Sprint 10 — Versão Release Candidate

**Prazo:** 14/11/2026 · **Status:** Planejada

### Entregas obrigatórias (Teams)

1. Sistema estável
2. Interface final
3. Banco de dados final
4. APIs documentadas (Swagger `/docs` + texto no PDF)
5. README atualizado (equipe, install, DB, execução)

### Checklist WarehouseFlow

* `docker compose up --build` estável
* Telas padronizadas
* Schema final coerente com o código
* Swagger cobrindo auth, CRUD e `/optimization/route`
* README com todos os itens pedidos pela professora

---

## Sprint 11 — Preparação para entrega

**Prazo:** 21/11/2026 · **Status:** Planejada

### Entregas obrigatórias (Teams)

1. Manual do Usuário
2. Manual Técnico (incluir seção do **motor de otimização**)
3. Documentação final consolidada
4. Revisão completa do código
5. Organização do GitHub (sem secrets, commits ok)

### Artefatos sugeridos no repo

* `docs/manual-usuario.md`
* `docs/manual-tecnico.md`
* Links no PDF se os manuais forem arquivos separados

---

## Sprint 12 — Versão final do sistema

**Prazo:** 28/11/2026 · **Status:** Planejada

### Entregas obrigatórias (Teams)

1. Sistema completamente finalizado (com otimização integrada)
2. Correção de todos os bugs
3. Code Freeze (tag/release no GitHub)
4. Preparação dos 2 vídeos (horizontal 16:9 ≤10 min; vertical 9:16 Instagram)
5. Ensaio completo da apresentação

### Conteúdo dos vídeos (planejar)

* Horizontal: problema, solução, arquitetura, demo real, **motor + métricas**
* Vertical: criativo; marcar `@pryscillabgoncalves` e `@antenorparnaiba`

---

## Entrega final — Fábrica de Software

**Prazo definitivo:** **05/12/2026** 23:59 · **Sem prorrogação**

### Entregas

1. Sistema funcional completo
2. Código-fonte no GitHub
3. Documentação (manuais, BD, arquitetura, instalação)
4. Vídeo horizontal (YouTube)
5. Vídeo vertical (Instagram, com marcações obrigatórias)

### PDF final no Teams

Nome do projeto, equipe, descrição, links (GitHub, docs, YouTube, Instagram), como executar, observações técnicas.

> Notas só são lançadas se as **atas** estiverem assinadas.

---

## Product Backlog resumido (por sprint de consolidação)

| ID | Item | Sprint |
|----|------|--------|
| PB-01 | Planejamento, RF/RNF, backlog, GitHub | 01 |
| PB-02 | Arquitetura, MER, protótipo, schema SQL | 02 |
| PB-03 | DB conectado, auth JWT, CRUD produtos, Compose | 03 |
| PB-04 | Módulo Produtos e Estoque completo (UI + validações) | 04 |
| PB-05 | Módulo Pedidos e Tarefas + testes | 05 |
| PB-06 | Módulo Otimização integrado + Pré-Banca | 06 |
| PB-07 | Dashboard, relatórios, filtros, logs, export | 07 |
| PB-08 | Permissões finais + usabilidade + revisão regras | 08 |
| PB-09 | Bateria de testes + docs atualizadas | 09 |
| PB-10 | Release Candidate | 10 |
| PB-11 | Manuais + organização GitHub | 11 |
| PB-12 | Code freeze + vídeos + ensaio | 12 |
| PB-13 | Entrega final 05/12 | Final |

---

## Equipe (identificar em todo PDF)

| Integrante | Matrícula |
|------------|----------:|
| Gabriel George de Araújo Figueiredo | 01605236 |
| Guilherme Branco Ferrario | 01596391 |
| João Pedro Silva de Araujo | 01606470 |
| Sérgio José de Araújo Júnior | 01590694 |
| Thiago de Morais Gonçalves | 01609695 |

---

## Observações para quem monta o relatório

1. Cada entrega no Teams é **um único PDF** com **todas as sprints anteriores + a atual**.
2. Sempre incluir **link do GitHub** e identificação de **todos** os integrantes.
3. Preferir **evidências executáveis** (prints de tela rodando, Swagger, Compose) a descrições vazias.
4. Qualquer mudança de escopo vs Sprint 01 deve ser **registrada e justificada**.
5. Destacar sempre o **motor de otimização + métricas** (exigência de Tópicos / feedback da professora).
