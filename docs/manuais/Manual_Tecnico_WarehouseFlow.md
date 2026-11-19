# Manual Técnico — WarehouseFlow

## 1. Introdução

Este manual descreve a arquitetura, estrutura, APIs, banco, frontend e
procedimentos de execução do WarehouseFlow. O conteúdo foi conferido com o
README, código, documentação existente e evidências do repositório.

Arquitetura:

```text
Navegador / Jinja
       |
       v
Nginx :8080 (Compose) ----> FastAPI :8000
                              |
                              +--> PostgreSQL :5433
                              +--> Motor NN + 2-opt
                              +--> optimization_runs
```

Tecnologias: Python, FastAPI, SQLAlchemy, Pydantic, JWT/python-jose, bcrypt,
Jinja2, JavaScript, HTML/CSS, PostgreSQL, Docker Compose e Pytest.

## 2. Arquitetura

- Frontend: templates Jinja em `frontend/templates`, CSS/JavaScript em
  `frontend/static`.
- Backend: aplicação FastAPI em `backend/app`.
- Banco: SQLAlchemy com PostgreSQL em produção/Compose; SQLite é usado nos
  testes em memória.
- Otimização: pacote puro em `backend/optimization`, integrado por serviços e
  rotas FastAPI.
- Proxy: Nginx encaminha a porta `8080` para a API `8000`.

## 3. Estrutura do repositório

| Caminho | Conteúdo |
|---|---|
| `backend/app/main.py` | Inicialização, handlers, páginas Jinja e registro dos routers |
| `backend/app/routers` | Endpoints HTTP |
| `backend/app/models` | Modelos SQLAlchemy |
| `backend/app/schemas` | Contratos Pydantic |
| `backend/app/services` | Orquestração |
| `backend/app/deps.py` | Usuário atual e autorização por perfil |
| `backend/app/security.py` | JWT, algoritmo e hash de senha |
| `backend/database` | DDL, seed, migração adicional e documentação do banco |
| `backend/optimization` | Motor NN + 2-opt |
| `frontend` | Templates e assets |
| `tests` | Pytest automatizado |
| `docs` | Documentação, sprints e evidências |
| `deploy/nginx.conf` | Configuração do proxy |
| `docker-compose.yml` | Postgres, API e frontend |

## 4. Tecnologias e dependências

Dependências verificadas em `requirements.txt`: FastAPI, Uvicorn, SQLAlchemy,
psycopg2-binary, Pydantic, email-validator, python-jose, bcrypt, python-dotenv,
Jinja2, python-multipart, httpx e pytest.

Versões do Python podem variar entre ambientes; os documentos de Sprint 11
referenciam Python 3.11+ e a execução atual foi realizada com Python 3.13.
Não fixe uma versão além do que puder ser confirmado no ambiente.

## 5. Banco de dados

### Tabelas principais

`roles`, `users`, `products`, `warehouses`, `locations`, `stock`, `orders`,
`order_items`, `tasks`, `optimization_results` e `optimization_runs`.

Relacionamentos:

- `users.role_id -> roles.id` com `ON DELETE SET NULL`;
- `locations.warehouse_id -> warehouses.id` com `ON DELETE CASCADE`;
- `stock.product_id -> products.id` e `stock.location_id -> locations.id`;
- `order_items.order_id -> orders.id` e `order_items.product_id -> products.id`;
- `tasks.order_id -> orders.id` e `tasks.assigned_user_id -> users.id`;
- `optimization_results.task_id -> tasks.id`;
- `optimization_runs` é a persistência oficial do motor; o DDL atual não cria
  FK físicas para todas as referências lógicas.

O MER consolidado está em
[docs/sprint-10/mer-final.md](../sprint-10/mer-final.md). DDL principal em
[backend/database/schema.sql](../../backend/database/schema.sql).

### Migrations e seeds

- `backend/database/schema.sql`: criação principal do banco.
- `backend/database/seed.sql`: dados iniciais.
- `backend/database/migrations/001_constraints.sql`: constraints adicionais.
- `backend/database/optimization_runs.sql`: tabela oficial do histórico.
- SQLAlchemy `Base.metadata.create_all(bind=engine)` também cria tabelas ORM
  presentes no processo.

## 6. Backend

O `app/main.py` configura handlers de validação e integridade, inclui routers,
monta arquivos estáticos e registra páginas Jinja.

Perfis definidos em `UserRole`: `ADMIN`, `GESTOR`, `OPERADOR`.

Autenticação:

- `POST /auth/login` valida e-mail/senha;
- gera JWT com subject do usuário;
- grava cookie HttpOnly `access_token`;
- `GET /auth/me` devolve o usuário atual;
- token Bearer ou cookie são aceitos nas rotas privadas.

O tempo de validade configurado é de 480 minutos.

Autorização:

- `require_role` protege endpoints por perfil;
- dependência `get_current_user` valida usuário, token e conta ativa;
- páginas HTML validam cookie e aplicam restrições adicionais em
  `/usuarios` e `/relatorios/movimentacoes`.

Erros:

- `400`: validação ou regra de integridade não tratada como duplicidade;
- `401`: sem autenticação ou token inválido/expirado;
- `403`: perfil sem permissão;
- `404`: recurso inexistente;
- `409`: duplicidade, vínculo ou conflito de negócio;
- `204`: operação sem corpo.

## 7. APIs

Consulte [docs/Api-doc.md](../Api-doc.md), Swagger `/docs` e OpenAPI
`/openapi.json`.

Principais áreas:

| Área | Prefixo |
|---|---|
| Autenticação | `/auth` |
| Produtos | `/products` |
| Estoque | `/stock` |
| Posições/armazéns | `/locations` |
| Pedidos/itens | `/orders` |
| Tarefas | `/tasks` |
| Usuários/cargos | `/users` |
| Relatórios | `/reports` |
| Otimização oficial | `/optimization` |
| Histórico legado | `/optimization-results` |

## 8. Frontend

Templates Jinja estão em `frontend/templates`. Páginas registradas incluem
login, início, dashboard, produtos, estoque, posições, pedidos, tarefas,
otimização, relatórios e usuários.

JavaScript:

- `auth.js` verifica `/auth/me`, aplica `data-roles` e executa logout;
- módulos específicos implementam CRUD, filtros e chamadas à API;
- o frontend não deve ser considerado fonte exclusiva de autorização; o backend
  aplica as restrições nas rotas.

## 9. Instalação e configuração

Pré-requisitos:

- Python compatível com as dependências;
- PostgreSQL ou Docker Desktop;
- Git.

Criação local do ambiente conhecido:

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Configure `.env` sem publicar valores reais. Para PostgreSQL no Compose,
`docker-compose.yml` sobrescreve `DATABASE_URL` para a rede interna.

Execução API no host com banco Docker:

```powershell
docker compose up -d db
python -m uvicorn app.main:app --app-dir backend --reload
```

Este conjunto foi documentado no README e deve ser testado novamente no
ambiente da equipe.

## 10. Docker

Serviços:

- `db`: PostgreSQL 16, porta host `5433`;
- `api`: FastAPI, porta `8000`;
- `frontend`: Nginx, porta `8080`;

Comandos documentados:

```powershell
docker compose up --build
docker compose up -d db
docker compose ps
docker compose logs api
docker compose logs db
docker compose down
```

O Compose não foi iniciado nesta etapa; o resultado de Docker/PostgreSQL
permanece pendente em cada ambiente local.

## 11. Testes

Comando geral já documentado e usado no repositório:

```powershell
python -m pytest -q
```

Comandos focados da Sprint 11:

```powershell
python -m pytest tests/test_api_optimization.py tests/test_optimization_flow_integration.py tests/test_optimization_reports.py tests/test_engine.py tests/test_distance.py tests/test_nearest_neighbor.py tests/test_two_opt.py -q
```

Teste ponta a ponta do motor:

```powershell
$env:PYTHONPATH = "backend"
python -m optimization.evidence_flow
```

Resultados registrados:

- Sprint 9: 92 aprovados, 1 ignorado, 1 aviso.
- Sprint 10: 101 aprovados, 2 ignorados.
- Sprint 11 do motor: 39 aprovados.
- Evidence flow: rota validada com distância antes `38`, depois `11`, redução
  aproximada de `71,05%`.

Não apresente esses resultados como validação integrada de Docker/PostgreSQL:
foram realizados em SQLite ou testes isolados conforme os relatórios.

## 12. Segurança

- `.env` está ignorado pelo Git.
- Não publique credenciais reais ou chaves JWT.
- `.env.example` contém placeholders, não credenciais reais.
- Senhas são armazenadas com bcrypt.
- Tokens expiram em 480 minutos.
- Cookies são HttpOnly e `SameSite=Lax`.
- `SECRET_KEY` deve ser aleatório e privado em cada ambiente.

Verificação de secrets: nenhum `.env` ou chave privada foi encontrado em
arquivos versionados nesta revisão. O relatório final deve ser atualizado caso
sejam adicionados novos artefatos.

## 13. Manutenção e evolução

- Novos endpoints: criar router, schemas e regra de autorização.
- Novos modelos: atualizar `app/models`, SQLAlchemy, schema SQL e migration.
- Novos testes: preservar a separação entre testes unitários, API e integração.
- Antes de publicar: executar os testes relevantes, validar Swagger e verificar
  navegação por perfil.
- Regressões: preservar evidências anteriores e anexar os resultados novos.
- Banco: testar migrations em cópia antes de aplicar em dados compartilhados.

## 14. Considerações finais

Docker, PostgreSQL e validação visual em navegador real continuam pendentes
neste ambiente. Todos os testes executados e bloqueios estão registrados em
documentos da Sprint 9, Sprint 10 e Sprint 11.
