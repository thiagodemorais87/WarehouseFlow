# WarehouseFlow

Sistema inteligente para gerenciamento e otimização de operações em armazéns e estoques.

## Figma Protótipo

https://www.figma.com/design/uGceagehdqafcFckYSlWZY/Sem-t%C3%ADtulo?node-id=5-569&t=kWlwVzC0cuJRlaCp-1

### Documentação oficial (sprints)

* [Proposta — problema → solução + métricas](docs/proposta.md)
* [Cronograma oficial — 12 sprints, datas e funcionalidades](docs/cronograma.md)
* [Motor de otimização (técnico)](docs/optimization.md)
* [Referência atual da API](docs/Api-doc.md)
* [Relatório da Sprint 10 — Release Candidate](docs/sprint-10/relatorio_rc_sprint10.md)
* [PDF acumulado Sprints 1–10 — Release Candidate](docs/Grupo26_WarehouseFlow_Sprint10_RC.pdf)
* [Repositório oficial no GitHub](https://github.com/thiagodemorais87/WarehouseFlow)

---

## 📦 Sobre o projeto

O **WarehouseFlow** é um sistema desenvolvido para auxiliar no gerenciamento de operações dentro de armazéns e estoques.

Diferentemente de um sistema tradicional baseado apenas em operações CRUD, o projeto possui como principal diferencial a utilização de um **motor de otimização**, responsável por analisar as tarefas operacionais e sugerir formas mais eficientes de executar atividades como separação, movimentação e distribuição de produtos.

O objetivo é utilizar dados do estoque e das operações para reduzir deslocamentos, melhorar a organização das tarefas e auxiliar os operadores na tomada de decisões.

---

## 🎯 Objetivo

Desenvolver um sistema capaz de gerenciar operações de armazém e utilizar algoritmos de otimização para sugerir a melhor sequência e organização das atividades operacionais.

### Objetivos específicos

* Gerenciar produtos;
* Controlar estoque;
* Gerenciar posições dentro do armazém;
* Registrar pedidos;
* Criar e controlar tarefas operacionais;
* Organizar tarefas de separação;
* Otimizar movimentações;
* Sugerir posições para armazenamento;
* Apresentar indicadores operacionais;
* Reduzir deslocamentos desnecessários;
* Auxiliar na tomada de decisão dos operadores.

---

## 👥 Equipe

| Integrante                          | Matrícula |
| ----------------------------------- | --------: |
| Gabriel George de Araújo Figueiredo |  01605236 |
| Guilherme Branco Ferrario           |  01596391 |
| João Pedro Silva de Araujo          |  01606470 |
| Sérgio José de Araújo Júnior        |  01590694 |
| Thiago de Morais Gonçalves          |  01609695 |

> **Turma:** 8MB.

**Responsabilidade desta entrega:** Guilherme Branco Ferrario — Documentação
e Testes. Os PDFs anteriores registram as atividades como “Pessoa 5 —
Integração, Testes e Documentação”, mas não identificam nominalmente as
Pessoas 1 a 4; não atribuímos esses papéis aos demais integrantes sem fonte.

---

## 🏭 Contexto

O projeto está inserido no contexto de **logística, armazenagem e gerenciamento de estoques**.

Operações de armazém envolvem diversas atividades que precisam ser executadas de forma organizada, como recebimento, armazenamento, separação de pedidos e movimentação de produtos.

Uma organização inadequada pode gerar deslocamentos desnecessários, aumento do tempo de separação, dificuldades de localização dos produtos e redução da eficiência operacional.

O WarehouseFlow busca utilizar os dados dessas operações para auxiliar na organização e otimização do trabalho.

---

## 💡 Problema

Em armazéns, a separação de pedidos (picking) muitas vezes segue a **ordem dos itens do pedido**, gerando deslocamentos longos entre posições. Sistemas convencionais de estoque resolvem cadastro e consulta (CRUD), mas **não calculam** uma sequência de visita melhor nem medem o ganho.

**Pergunta central:** como reduzir o deslocamento do operador na separação, com algoritmo próprio e métricas transparentes?

Detalhamento: [docs/proposta.md](docs/proposta.md).

---

## 🚀 Proposta da solução

O WarehouseFlow **não é só um WMS de CRUD**. Ele combina:

1. **Base operacional** — produtos, estoque, posições, pedidos, tarefas e usuários no PostgreSQL.
2. **Diferencial computacional** — motor próprio de otimização de rota de picking:
   * Nearest Neighbor + melhoria local **2-opt**;
   * distância Manhattan;
   * implementação em Python puro (sem OR-Tools / solvers externos);
   * endpoint `POST /optimization/route`.

```text
Ordem original das posições
       ↓
Nearest Neighbor
       ↓
2-opt
       ↓
Rota sugerida + métricas (distância, redução %, tempo ms)
```

---

## 🧠 Motor de otimização e métricas

O diferencial acadêmico do projeto é o motor em [`backend/optimization/`](backend/optimization/).

### Métricas de desempenho (calculadas)

| Métrica | Descrição |
|---------|-----------|
| `distance_before` | Distância da rota original |
| `nearest_neighbor_distance` | Distância após NN |
| `two_opt_distance` / `distance_after` | Distância após 2-opt |
| `distance_reduction` | Ganho absoluto de distância |
| `reduction_percent` | Ganho percentual |
| `execution_time_ms` | Tempo de execução |

Documentação completa: [docs/optimization.md](docs/optimization.md).

---

## 🛠️ Tecnologias

### Backend

* Python
* FastAPI
* SQLAlchemy
* Pydantic

### Banco de dados

* PostgreSQL

### Front-end

* HTML
* CSS
* Jinja2
* JavaScript

### Testes

* Pytest

### Infraestrutura

* Docker
* Docker Compose

### Versionamento

* Git
* GitHub

* JavaScript é utilizado na interface para consumir a API e apoiar login,
  navegação e formulários.

---

## 🏗️ Arquitetura inicial

```text
┌─────────────────────────┐
│       Front-end         │
│      HTML + CSS         │
│       Jinja2            │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│        Backend          │
│        FastAPI          │
├─────────────────────────┤
│ Regras de negócio       │
│ APIs                    │
│ Serviços                │
└────────────┬────────────┘
             │
       ┌─────┴─────┐
       ▼           ▼
┌────────────┐ ┌──────────────┐
│ PostgreSQL │ │ Optimization │
│            │ │    Engine    │
└────────────┘ └──────────────┘
```

---

## 📋 Principais funcionalidades

### Produtos

* Cadastro de produtos;
* Consulta de produtos;
* Atualização;
* Exclusão.

### Estoque

* Controle de quantidade;
* Entradas;
* Saídas;
* Localização dos produtos.

### Armazém

* Cadastro de armazéns;
* Cadastro de posições;
* Controle da ocupação das posições.

### Pedidos

* Criação, consulta, atualização e exclusão de pedidos de entrada/saída;
* Gerenciamento de itens com quantidade positiva;
* Status `PENDING`, `PROCESSING`, `COMPLETED` e `CANCELLED`.

### Tarefas

* Criação e consulta de tarefas `PICKING`, `PUTAWAY` e `REPLENISHMENT`;
* Atribuição a usuário e atualização de status;
* OPERADOR limitado às tarefas atribuídas a si.

### Otimização

* Sequenciamento de picking pelo motor Nearest Neighbor + 2-opt;
* Otimização por lista de posições ou por pedido OUTBOUND;
* Histórico, métricas e relatório CSV de otimizações.

### Usuários e relatórios

* Cadastro/consulta/atualização/exclusão de usuários e cargos pela API, com
  senha armazenada como hash e regras RBAC;
* Dashboard autenticado, relatórios de pedidos e movimentações de estoque;
* Exportação CSV dos relatórios. Não há página de administração de usuários.

---

## 📊 Status do projeto

**Sprint 10 — Release Candidate (documentação e testes).** O repositório
contém JWT/RBAC, módulos de produtos/estoque/posições, pedidos e tarefas,
dashboard, relatórios com CSV e motor de picking NN + 2-opt. A administração
de usuários está disponível pela API; não há tela de usuários no menu atual.

Na validação local de 13/11/2026, a API e as páginas foram exercitadas contra
uma base SQLite descartável. O Pytest concluiu com **101 passed, 2 skipped**.
O Swagger/OpenAPI respondeu em `/docs` e `/openapi.json`. O Compose foi
validado estaticamente, mas não iniciado: o daemon Docker não estava
disponível; portanto a integração real com PostgreSQL e Nginx permanece
pendente. Evidências e ressalvas: [relatório RC](docs/sprint-10/relatorio_rc_sprint10.md).

O cronograma mantém Sprints 11 e 12 planejadas: manuais/code review e
preparação da versão final, code freeze e ensaio, respectivamente. Consulte o
[cronograma oficial](docs/cronograma.md).

---

## 📁 Estrutura do projeto

```text
warehouseflow/
│
├── backend/
│   ├── app/
│   │   ├── routers/         # HTTP: CRUD + auth + motor (/optimization/route)
│   │   ├── models/          # SQLAlchemy
│   │   ├── schemas/         # Pydantic
│   │   ├── services/        # Orquestração (ex.: optimization_service)
│   │   ├── deps.py          # JWT / RBAC
│   │   ├── security.py      # Hash e tokens
│   │   ├── database.py      # Engine SQLAlchemy
│   │   └── main.py          # App FastAPI + páginas Jinja
│   ├── database/            # schema.sql, seed.sql e migrations SQL
│   └── optimization/        # Motor puro (NN + 2-opt), sem DB
├── frontend/                # Templates Jinja + static (CSS/JS)
├── docs/
│   ├── proposta.md
│   ├── cronograma.md
│   └── optimization.md
├── tests/
├── deploy/
│   └── nginx.conf           # Proxy UI :8080 → api:8000
├── Dockerfile
├── docker-compose.yml       # Postgres + API + nginx
├── .env.example
├── .gitignore
├── requirements.txt
├── pytest.ini
└── README.md
```

---

## 🚀 Deploy local

### Opção A — tudo no Docker (recomendado)

Pré-requisito: Docker Desktop.

Crie `.env` somente se ainda não existir; consulte `.env.example` e ajuste as
configurações sem substituir um `.env` já existente.

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
docker compose up --build
```

Em Linux/macOS:

```bash
[ -f .env ] || cp .env.example .env
docker compose up --build
```

Sobe **PostgreSQL** (5433), **API/otimizador** (8000) e **frontend** via nginx (8080) juntos.

* Frontend (UI): http://127.0.0.1:8080/ (redireciona para `/login`)
* Login / Dashboard / Produtos / Estoque / Posições: http://127.0.0.1:8080/login , `/dashboard`, `/produtos`, `/estoque`, `/posicoes`
* Backend API: http://127.0.0.1:8000
* Swagger UI: http://127.0.0.1:8000/docs
* OpenAPI JSON: http://127.0.0.1:8000/openapi.json
* Health: http://127.0.0.1:8000/health
* Postgres (host): `localhost:5433` (user/senha/db: `warehouse` / `warehouse` / `warehouseflow`)

Login de demo (seed): `admin@warehouseflow.com` / `admin123`.

O Postgres aplica `backend/database/schema.sql` + `seed.sql` na primeira inicialização.
Volumes montam `backend/` e `frontend/` com hot-reload (`--reload`) no serviço `api`.
O serviço `frontend` (nginx) faz proxy de tudo em `:8080` para a API, mantendo as URLs relativas do JS.

#### Versão do projeto (`APP_VERSION`)

A imagem da API e o endpoint `/health` expõem a versão alinhada à tag/GitHub Release.

1. No `.env`, defina `APP_VERSION` igual à tag da release (ex.: `v1.0.0`). Sem release, use `dev` (padrão do `.env.example`).
2. No GitHub: crie uma tag `vX.Y.Z` e uma **Release** (*Releases → New release*).
3. Suba de novo com `docker compose up --build` e confira:
   * `GET http://127.0.0.1:8000/health` → `{"status":"ok","version":"v1.0.0"}`
   * Swagger (`/docs`) mostra a mesma versão no título da API
   * Labels da imagem: `org.opencontainers.image.version` (via `docker inspect warehouseflow-api`)

### Opção B — API no host + banco no Docker

PowerShell:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
docker compose up -d db
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --app-dir backend --reload
```

Linux/macOS:

```bash
[ -f .env ] || cp .env.example .env
docker compose up -d db
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --app-dir backend --reload
```

No `.env`, use `localhost:5433` (não `db`) na `DATABASE_URL`. A UI fica em http://127.0.0.1:8000/ (redirect para `/login`, mesmo processo da API).

### Testes do motor

```bash
python -m pytest -q
```

Os testes usam a configuração definida em `pytest.ini`; os testes de integração
não exigem que o Docker esteja ativo. Em PowerShell, ative
`.venv\Scripts\Activate.ps1` antes de executar.

### Endpoints principais

| Área | Endpoint |
|------|----------|
| Produtos (CRUD) | `/products` |
| Estoque | `/stock` |
| Pedidos | `/orders` |
| Tarefas | `/tasks` |
| Posições | `/locations` |
| Usuários | `/users` |
| Resultados salvos | `/optimization-results` |
| Motor de rota | `POST /optimization/route` |

Documentação do motor: [docs/optimization.md](docs/optimization.md) · [backend/optimization/README.md](backend/optimization/README.md)

Contrato de autenticação, pedidos, tarefas, usuários, relatórios e otimização:
[docs/Api-doc.md](docs/Api-doc.md). A API de usuários existe; uma tela de
administração de usuários não está implementada no menu atual.

---

## 🔀 Git Flow

As alterações deverão ser desenvolvidas através de branches.

Exemplo:

```text
main
 │
 ├── develop
 │    │
 │    ├── feature/database
 │    ├── feature/products-api
 │    ├── feature/stock-api
 │    ├── feature/optimization-engine
 │    └── feature/frontend
```

Pull Requests deverão ser utilizados para integrar as alterações ao branch principal de desenvolvimento.

---

## 📌 Organização do projeto

O acompanhamento do desenvolvimento será realizado através do **GitHub Projects**, utilizando um quadro Kanban.

### Fluxo

```text
Backlog
   ↓
A Fazer
   ↓
Em Desenvolvimento
   ↓
Em Revisão
   ↓
Em Testes
   ↓
Concluído
```

Cada funcionalidade deverá ser registrada como uma Issue e associada ao respectivo Sprint.

---

## 📚 Documentação

A documentação do projeto será mantida no diretório:

```text
/docs
```

Incluindo:

* [Proposta oficial](docs/proposta.md);
* [Cronograma com sprints semanais e datas](docs/cronograma.md);
* [Motor de otimização](docs/optimization.md);
* [Referência da API](docs/Api-doc.md) e Swagger em `http://127.0.0.1:8000/docs`;
* [Relatório da Sprint 10 — Release Candidate](docs/sprint-10/relatorio_rc_sprint10.md);
* Requisitos e PDF da Sprint 01;
* Banco de dados;
* Documentação técnica.

---

## 👨‍💻 Projeto acadêmico

Projeto desenvolvido para a disciplina de **Fábrica de Software**.

**WarehouseFlow — Sistema Inteligente de Gerenciamento e Otimização de Armazéns**
