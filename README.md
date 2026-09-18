# WarehouseFlow

Sistema inteligente para gerenciamento e otimização de operações em armazéns e estoques.

## Figma Prototiopo

https://www.figma.com/design/uGceagehdqafcFckYSlWZY/Sem-t%C3%ADtulo?node-id=5-569&t=kWlwVzC0cuJRlaCp-1


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

Como auxiliar na organização e execução das operações de um armazém de forma mais eficiente, reduzindo deslocamentos desnecessários e melhorando a priorização das tarefas?

---

## 🚀 Proposta da solução

O WarehouseFlow centralizará as informações do armazém e utilizará um motor de otimização para analisar as operações.

O sistema poderá considerar fatores como:

* localização dos produtos;
* distância entre posições;
* prioridade dos pedidos;
* quantidade de produtos;
* disponibilidade de estoque;
* capacidade das posições;
* tarefas pendentes.

A partir dessas informações, o sistema poderá gerar recomendações para melhorar a execução das atividades.

---

## 🧠 Motor de otimização

O principal diferencial do projeto será o motor de otimização.

Em vez de simplesmente armazenar informações, o sistema deverá utilizar os dados disponíveis para gerar recomendações.

Exemplo:

```text
Pedidos pendentes
       ↓
Produtos necessários
       ↓
Localização dos produtos
       ↓
Distâncias
       ↓
Prioridade dos pedidos
       ↓
Algoritmo de otimização
       ↓
Sequência sugerida de tarefas
```

A primeira versão do algoritmo terá como objetivo minimizar deslocamentos e organizar a sequência de execução das tarefas.

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

**Em desenvolvimento — Sprint 02 (integração)**

### Entregas

* [x] Banco de dados conectado (PostgreSQL + SQLAlchemy)
* [ ] Login funcional (branch `feature/auth-users` — outro integrante)
* [x] Cadastro de usuários via API (`/users` — hash definitivo na sprint de auth)
* [ ] Controle de perfis com enforcement (auth)
* [x] CRUD principal (`/products`, estoque, pedidos, tarefas, posições)
* [x] Deploy local (Docker Compose + instruções abaixo)
* [x] Motor de otimização (`POST /optimization/route`)

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
│   └── optimization.md
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
├── pytest.ini
├── docker-compose.yml
└── README.md
```

---

## 🚀 Deploy local

### 1. Pré-requisitos

* Python 3.11+
* Docker Desktop (para o PostgreSQL)

### 2. Banco de dados

```bash
docker compose up -d
```

Isso sobe o Postgres na porta `5432` e aplica `backend/database/schema.sql` + `seed.sql` na primeira inicialização.

### 3. Variáveis de ambiente

```bash
cp .env.example .env
```

O valor padrão já aponta para o container:

`postgresql+psycopg2://warehouse:warehouse@localhost:5432/warehouseflow`

### 4. Dependências e API

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --app-dir backend --reload
```

* API / Swagger: http://127.0.0.1:8000/docs
* Health: http://127.0.0.1:8000/health
* Shell de login (UI estática): http://127.0.0.1:8000/login

### 5. Testes do motor

```bash
pytest -q
```

### 6. Endpoints principais

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

* Requisitos;
* Casos de uso;
* Diagramas;
* Arquitetura;
* Banco de dados;
* Motor de otimização;
* Documentação técnica.

---

## 👨‍💻 Projeto acadêmico

Projeto desenvolvido para a disciplina de **Fábrica de Software**.

**WarehouseFlow — Sistema Inteligente de Gerenciamento e Otimização de Armazéns**
