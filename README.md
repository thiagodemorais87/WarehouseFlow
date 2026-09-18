# WarehouseFlow

Sistema inteligente para gerenciamento e otimização de operações em armazéns e estoques.

## Figma Protótipo

https://www.figma.com/design/uGceagehdqafcFckYSlWZY/Sem-t%C3%ADtulo?node-id=5-569&t=kWlwVzC0cuJRlaCp-1

### Documentação oficial (feedback acadêmico + sprints)

* [Proposta — problema → solução + métricas](docs/proposta.md)
* [Cronograma oficial — 12 sprints, datas e funcionalidades](docs/cronograma.md)
* [Motor de otimização (técnico)](docs/optimization.md)

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

> **Turma:** 8MA - Manha

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
* Bootstrap

### Testes

* Pytest

### Infraestrutura

* Docker
* Docker Compose

### Versionamento

* Git
* GitHub

> O projeto não utilizará JavaScript.

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

* Cadastro de pedidos;
* Itens dos pedidos;
* Status dos pedidos;
* Prioridade.

### Tarefas

* Separação;
* Movimentação;
* Distribuição;
* Priorização;
* Controle de status.

### Otimização

* Sugestão de posição;
* Priorização de tarefas;
* Sequenciamento de separação;
* Otimização de deslocamentos.

---

## 📊 Status do projeto

**Em andamento — Sprints 02 e 03** (prazo comum **19/09/2026**) · [cronograma oficial completo](docs/cronograma.md)

### Entregas da disciplina (visão rápida)

* [x] Sprint 01 — Planejamento (05/09/2026)
* [ ] Sprint 02 — Arquitetura e modelagem (19/09/2026)
* [ ] Sprint 03 — Estrutura inicial (DB, auth, CRUD, deploy) (19/09/2026)
* [ ] Sprint 04 — Módulo 1: Produtos e Estoque (26/09/2026)
* [ ] Sprint 05 — Módulo 2: Pedidos e Tarefas (03/10/2026)
* [ ] Sprint 06 — Módulo 3: Otimização + Pré-Banca (17/10/2026)
* [ ] Sprints 07–12 + entrega final 05/12/2026 — ver cronograma

### Situação técnica atual no repositório

* [x] Banco de dados conectado (PostgreSQL + SQLAlchemy)
* [ ] Login funcional JWT (necessário para Sprint 03 — `feature/auth-users`)
* [x] Cadastro de usuários via API (`/users` — hash definitivo na auth)
* [ ] Controle de perfis com enforcement (Sprint 03/08)
* [x] CRUD principal API (`/products` e demais entidades)
* [x] Deploy local (Docker Compose API + banco)
* [x] Motor de otimização com métricas (`POST /optimization/route`)
* [x] Proposta + cronograma oficiais ([docs/proposta.md](docs/proposta.md), [docs/cronograma.md](docs/cronograma.md))

---

## 📁 Estrutura do projeto

```text
warehouseflow/
│
├── backend/
│   ├── app/                 # FastAPI (API, routers CRUD, schemas, services)
│   ├── database/            # schema.sql + seed.sql
│   └── optimization/        # Motor puro (NN + 2-opt), sem DB
├── frontend/                # Templates Jinja + static (shell de login)
├── docs/
│   ├── proposta.md          # Proposta oficial (problema → solução + métricas)
│   ├── cronograma.md        # 12 sprints oficiais + funcionalidades por sprint
│   └── optimization.md      # Detalhe técnico do motor
├── tests/
├── Dockerfile               # Imagem da API (serviço api no Compose)
├── docker-compose.yml       # Postgres + API
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

```bash
docker compose up --build
```

Sobe **PostgreSQL** + **API** (CRUD, motor de otimização e shell de login) juntos.

* API / Swagger: http://127.0.0.1:8000/docs
* Health: http://127.0.0.1:8000/health
* Shell de login (UI estática): http://127.0.0.1:8000/login

O Postgres aplica `backend/database/schema.sql` + `seed.sql` na primeira inicialização.
Volumes montam `backend/` e `frontend/` com hot-reload (`--reload`).

> **Telas:** hoje só existe a página `/login` (sem auth real). CRUD e otimização testam-se em `/docs` e `POST /optimization/route`.

### Opção B — API no host + banco no Docker

```bash
docker compose up -d db
cp .env.example .env
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --app-dir backend --reload
```

No `.env`, use `localhost` (não `db`) na `DATABASE_URL`.

### Testes do motor

```bash
pytest -q
```

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

> **Auth:** login JWT, hash bcrypt e enforcement de perfis serão entregues em `feature/auth-users`.

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
* Requisitos e PDF da Sprint 01;
* Banco de dados;
* Documentação técnica.

---

## 👨‍💻 Projeto acadêmico

Projeto desenvolvido para a disciplina de **Fábrica de Software**.

**WarehouseFlow — Sistema Inteligente de Gerenciamento e Otimização de Armazéns**
