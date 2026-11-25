# 🗄️ WarehouseFlow — Documentação do Banco de Dados

Esta pasta contém a modelagem, scripts DDL/DML e instruções de execução para o banco de dados relacional do **WarehouseFlow**, sistema inteligente de gerenciamento e otimização de operações em armazéns.

---

## 📁 Estrutura do Diretório

```text
backend/database/
├── schema.sql              # DDL OFICIAL (único usado pelo Compose): 11 tabelas, chaves, CHECKs e relacionamentos
├── seed.sql                # Dados de demonstração determinísticos e idempotentes (inclui optimization_runs)
├── optimization_runs.sql   # Cópia dedicada do DDL do histórico, para bancos antigos (idêntica ao trecho do schema)
├── migrations/             # Ajustes para bancos já existentes (001 constraints, 002 alinhamento do schema)
└── README.md               # Documentação do modelo de dados e instruções
```

---

## 📊 Modelo Entidade-Relacionamento (DER)

O banco foi projetado no **PostgreSQL** para suportar a gestão operacional de armazém e integrar com o motor de otimização de rotas e estocagem (*slotting*).

### Lista de Entidades e Tabelas

1. **`roles`**: Cargos e níveis de acesso dos usuários (`ADMIN`, `GESTOR`, `OPERADOR`).
2. **`users`**: Cadastro de usuários/operadores do sistema.
3. **`warehouses`**: Armazéns ou depósitos físicos.
4. **`locations`**: Posições específicas dentro do armazém (Corredor, Estante, Prateleira).
5. **`products`**: Catálogo de produtos com dimensões (peso e volume para cálculo de otimização).
6. **`stock`**: Saldo de estoque por produto e por posição física.
7. **`orders`**: Pedidos de operação de entrada (`INBOUND`) ou saída (`OUTBOUND`).
8. **`order_items`**: Itens solicitados em cada pedido.
9. **`tasks`**: Tarefas operacionais vinculadas aos pedidos (ex: `PICKING`, `PUTAWAY`, `REPLENISHMENT`).
10. **`optimization_results`** (**legado / deprecated**): CRUD de resultados ligados a `task_id` (JSON/score). **Não** é alimentado pelo pipeline NN + 2-opt. Preferir `optimization_runs`.
11. **`optimization_runs`** (**oficial — motor**): Histórico de cada execução do motor (NN + 2-opt), com rotas intermediárias, métricas de distância/redução e vínculo lógico a usuário/pedido. Gravado pelos POSTs em `/optimization/*`.

---

## 📐 Dicionário de Dados

### 1. `roles`
| Coluna | Tipo | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PK | Identificador único |
| `name` | VARCHAR(50) | UNIQUE, NOT NULL | Nome do papel: `ADMIN`, `GESTOR` ou `OPERADOR` |

### 2. `users`
| Coluna | Tipo | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PK | Identificador único |
| `name` | VARCHAR(100) | NOT NULL | Nome completo do usuário |
| `email` | VARCHAR(100) | UNIQUE, NOT NULL | E-mail do usuário |
| `password_hash` | VARCHAR(255) | NOT NULL | Senha criptografada |
| `role_id` | INTEGER | FK -> roles(id) ON DELETE SET NULL | Papel/Cargo do usuário (opcional; sem papel o usuário fica sem acesso às rotas protegidas) |
| `is_active` | BOOLEAN | NOT NULL DEFAULT TRUE | Usuário inativo não consegue entrar |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Data de criação |

### 3. `products`
| Coluna | Tipo | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PK | Identificador único |
| `sku` | VARCHAR(50) | UNIQUE, NOT NULL | Código SKU do produto |
| `name` | VARCHAR(150) | NOT NULL | Nome do produto |
| `description` | TEXT | NULL | Descrição detalhada |
| `weight` | DECIMAL(10,2) | NULL | Peso unitário em kg |
| `volume` | DECIMAL(10,2) | NULL | Volume unitário em m³ |
| *Constraint* | `ck_products_weight_non_negative`, `ck_products_volume_non_negative` | CHECK (>= 0 ou NULL) | Peso e volume nunca negativos |

### 4. `warehouses`
| Coluna | Tipo | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PK | Identificador único |
| `name` | VARCHAR(100) | NOT NULL | Nome do armazém |
| `address` | TEXT | NULL | Endereço físico |

### 5. `locations`
| Coluna | Tipo | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PK | Identificador único |
| `warehouse_id` | INTEGER | FK -> warehouses(id) ON DELETE CASCADE | Armazém ao qual pertence (opcional no banco; a API exige) |
| `code` | VARCHAR(20) | UNIQUE, NOT NULL | Código legível da posição (Ex: A1-05-B) |
| `aisle` | VARCHAR(10) | NULL | Corredor |
| `rack` | VARCHAR(10) | NULL | Estante / Prateleira vertical |
| `shelf` | VARCHAR(10) | NULL | Nível / Nivelamento |
| `is_active` | BOOLEAN | NOT NULL DEFAULT TRUE | Status de operação da posição (inativa não recebe estoque) |

### 6. `stock`
| Coluna | Tipo | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PK | Identificador único |
| `product_id` | INTEGER | NOT NULL, FK -> products(id) ON DELETE CASCADE | Produto em estoque |
| `location_id` | INTEGER | NOT NULL, FK -> locations(id) ON DELETE CASCADE | Posição no armazém |
| `quantity` | INTEGER | NOT NULL DEFAULT 0 | Quantidade disponível |
| `last_updated` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | ÚLtima atualização |
| *Constraint* | UNIQUE(product_id, location_id) | | Impede duplicidade do mesmo produto na mesma vaga |
| *Constraint* | `ck_stock_quantity_non_negative` | CHECK (quantity >= 0) | Saldo nunca negativo |

### 7. `orders`
| Coluna | Tipo | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PK | Identificador único |
| `type` | VARCHAR(20) | NOT NULL, CHECK (`INBOUND`, `OUTBOUND`) | Tipo: `INBOUND` ou `OUTBOUND` |
| `status` | VARCHAR(20) | NOT NULL DEFAULT 'PENDING', CHECK | Status: `PENDING`, `PROCESSING`, `COMPLETED`, `CANCELLED` |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Data do pedido |

### 8. `order_items`
| Coluna | Tipo | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PK | Identificador único |
| `order_id` | INTEGER | NOT NULL, FK -> orders(id) ON DELETE CASCADE | Pedido associado |
| `product_id` | INTEGER | NOT NULL, FK -> products(id) ON DELETE RESTRICT | Produto (não pode ser excluído enquanto constar em pedido) |
| `quantity` | INTEGER | NOT NULL, CHECK (quantity > 0) | Quantidade solicitada |

### 9. `tasks`
| Coluna | Tipo | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PK | Identificador único |
| `type` | VARCHAR(30) | NOT NULL, CHECK | Tipo de tarefa (`PICKING`, `PUTAWAY`, `REPLENISHMENT`) |
| `status` | VARCHAR(20) | NOT NULL DEFAULT 'PENDING', CHECK | Status (`PENDING`, `IN_PROGRESS`, `COMPLETED`) |
| `order_id` | INTEGER | NOT NULL, FK -> orders(id) ON DELETE CASCADE | Pedido origem |
| `assigned_user_id` | INTEGER | FK -> users(id) ON DELETE SET NULL | Operador atribuído (opcional) |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Data de criação |

### 10. `optimization_results` (legado / deprecated)

CRUD por `task_id` via `/optimization-results`. **Não** recebe gravações do motor NN + 2-opt. Mantida por compatibilidade; caminho oficial é `optimization_runs`.

| Coluna | Tipo | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PK | Identificador único |
| `task_id` | INTEGER | NOT NULL, FK -> tasks(id) ON DELETE CASCADE | Tarefa associada |
| `suggested_location_id` | INTEGER | FK -> locations(id) (sem ON DELETE: NO ACTION) | Posição sugerida pelo algoritmo (opcional); a API bloqueia excluir posição usada |
| `suggested_route` | JSONB | NULL | Sequência otimizada de passos/rotas em JSON |
| `score` | DECIMAL(10,4) | NULL | Métrica de eficiência / custo da solução |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Data de geração do cálculo |

### 11. `optimization_runs` (oficial — motor)

Histórico oficial do motor de rota (persistência best-effort após `POST /optimization/route`, `/route/by-order` e `/route/batch`).  
Referências a `users` (`user_id`) e `orders` (`order_id`) são **lógicas** (sem FK CASCADE no DDL atual), alinhadas ao model SQLAlchemy.

| Coluna | Tipo | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PK | Identificador único |
| `user_id` | INTEGER | NOT NULL | Usuário que disparou a otimização |
| `user_email` | VARCHAR(100) | NOT NULL | E-mail do usuário no momento da execução |
| `executed_at` | TIMESTAMP | NOT NULL DEFAULT CURRENT_TIMESTAMP | Data/hora da execução |
| `source` | VARCHAR(20) | NOT NULL | Origem (`route`, `by-order` ou `batch`) |
| `order_id` | INTEGER | NULL | Pedido associado (quando `by-order` ou `batch`) |
| `original_route` | JSONB | NOT NULL | Rota original (antes do algoritmo) |
| `nearest_neighbor_route` | JSONB | NOT NULL | Rota após Nearest Neighbor |
| `two_opt_route` | JSONB | NOT NULL | Rota final após 2-opt |
| `distance_before` | DOUBLE PRECISION | NOT NULL | Distância da rota original |
| `nearest_neighbor_distance` | DOUBLE PRECISION | NOT NULL | Distância após NN |
| `two_opt_distance` | DOUBLE PRECISION | NOT NULL | Distância após 2-opt |
| `distance_after` | DOUBLE PRECISION | NOT NULL | Distância final (= `two_opt_distance`) |
| `distance_reduction` | DOUBLE PRECISION | NOT NULL | Ganho absoluto de distância |
| `reduction_percent` | DOUBLE PRECISION | NOT NULL | Ganho percentual |
| `execution_time_ms` | DOUBLE PRECISION | NOT NULL | Tempo de execução do motor (ms) |
| `locations_count` | INTEGER | NOT NULL | Quantidade de posições na rota |

Índices: `ix_optimization_runs_id`, `ix_optimization_runs_executed_at` (DESC).

DDL oficial: tabela 11 do [`schema.sql`](schema.sql), único arquivo de DDL montado no Compose. [`optimization_runs.sql`](optimization_runs.sql) é a cópia para bancos antigos (um teste garante que são idênticas).

---

## Como Executar o Banco de Dados

# Pré-requisitos e Setup do Banco de Dados

## Pré-requisitos
* **PostgreSQL 15+** instalado e em execução na máquina local
* **Utilitários de linha de comando** (`psql`, `createdb`) configurados no `PATH` **OU** cliente gráfico (*DBeaver*, *pgAdmin*)

---

## Linha de Comando (`psql`) — Local

### 1. Criar o Banco de Dados
No terminal, execute o comando abaixo para criar a base `warehouseflow`:

```bash
createdb -U postgres warehouseflow
```
*(Caso peça senha, informe a senha cadastrada na instalação do seu PostgreSQL).*

### 2. Executar o DDL (`schema.sql`)
Estando na raiz do projeto, rode o script para criar a estrutura completa de tabelas (já inclui `optimization_runs`):

```bash
psql -U postgres -d warehouseflow -f backend/database/schema.sql
```

Em um banco **antigo** que ainda não tenha a tabela do histórico (a API também a cria sozinha ao iniciar), aplique, de forma idempotente:

```bash
psql -U postgres -d warehouseflow -f backend/database/optimization_runs.sql
```

### 3. Popular com a Massa de Testes (`seed.sql`)
Execute o script DML para inserir os registros iniciais nas tabelas:

```bash
psql -U postgres -d warehouseflow -f backend/database/seed.sql
```

---

### Dados de demonstração (o que o seed cria)

O `seed.sql` é **determinístico** (ids e datas fixos) e **idempotente** (`ON CONFLICT` em todos os `INSERT`: rodar de novo não duplica nada). Ele foi montado para o dashboard e os relatórios mostrarem algo útil na apresentação:

| Tabela | Registros | O que demonstra |
| :--- | :---: | :--- |
| `roles` / `users` | 3 / 3 | Um usuário por perfil |
| `warehouses` / `locations` | 1 / 5 | Armazém Central Recife, posições A1 e B1 |
| `products` | 5 | `PROD-001` a `PROD-005` |
| `stock` | 5 | 164 unidades; `PROD-004` (6) e `PROD-005` (3) em **estoque baixo** |
| `orders` | 6 | Todos os status (2 PENDING, 1 PROCESSING, 2 COMPLETED, 1 CANCELLED) e os dois tipos (4 OUTBOUND, 2 INBOUND), de 18 a 28/10/2026 |
| `order_items` | 9 | Itens de todos os pedidos |
| `tasks` | 4 | PENDING (2), IN_PROGRESS (1), COMPLETED (1); uma sem responsável |
| `optimization_results` | 1 | Sugestão de rota da tarefa 1 |
| `optimization_runs` | 3 | Redução média de **14,67** de distância (25% em média), por 3 usuários diferentes |

**Logins** (senha de todos: `admin123`): `admin@warehouseflow.com` (ADMIN), `maria.gestora@warehouseflow.com` (GESTOR), `joao.operador@warehouseflow.com` (OPERADOR).

**Voltar a demonstração ao estado original:** o Compose só executa `schema.sql` e `seed.sql` quando o volume do banco está vazio, então para recomeçar do zero:

```bash
docker compose down -v      # apaga o volume (todos os dados criados pela API)
docker compose up --build -d
```

Para **manter os dados** e só aplicar os ajustes de schema num banco existente:

```bash
docker compose exec -T db psql -U warehouse -d warehouseflow -v ON_ERROR_STOP=1 -f /migrations/001_constraints.sql
docker compose exec -T db psql -U warehouse -d warehouseflow -v ON_ERROR_STOP=1 -f /migrations/002_alinha_schema.sql
```

## 📄 Relacionamentos: PDF e Mermaid

O diagrama de relacionamentos, a tabela de chaves estrangeiras (com cardinalidade e `ON DELETE`), o dicionário de dados completo e as regras de integridade estão em:

* [`docs/Modelo_Relacional_WarehouseFlow.pdf`](../../docs/Modelo_Relacional_WarehouseFlow.pdf): para anexar ao relatório da sprint.
* [`docs/modelo-relacional.md`](../../docs/modelo-relacional.md): versão em Mermaid, que o GitHub renderiza.

Os dois são **gerados** a partir do `schema.sql` e dos modelos, para nunca divergirem do banco. Depois de mudar o schema, regenere:

```bash
pip install reportlab           # só para gerar o PDF
python scripts/gerar_pdf_relacionamentos.py
```

## ✅ Verificações automáticas do schema e do seed

| Teste | O que garante |
| :--- | :--- |
| `tests/test_schema_coerente.py` | O `schema.sql` aplicado num PostgreSQL real é igual aos modelos (tabelas, colunas, tipos, NOT NULL, PK, FK com `ON DELETE`, UNIQUE e CHECK); `optimization_runs.sql` é idêntico ao trecho do schema; o Compose monta só `schema.sql` e `seed.sql` |
| `tests/test_seed_final.py` | Seed idempotente (rodado duas vezes), com contagens, status, estoque baixo e métricas de otimização coerentes, e sem colisão de ids nos próximos registros |

Os testes que usam banco exigem `TEST_DATABASE_URL` (um PostgreSQL **de teste**, ele usa um schema temporário e não toca no público); sem a variável eles são pulados:

```bash
TEST_DATABASE_URL=postgresql+psycopg2://warehouse:warehouse@localhost:5433/warehouseflow_test pytest tests/test_schema_coerente.py tests/test_seed_final.py
```

## Migrations (como evoluir o schema)

O projeto **não usa Alembic**: as mudanças de schema são **scripts SQL idempotentes** em `backend/database/migrations/`, numerados em ordem. Cada um pode ser executado mais de uma vez e, se houver dado que viole a nova regra, para com uma mensagem explicando o que corrigir (nada é apagado automaticamente).

| Script | O que faz |
| :--- | :--- |
| `001_constraints.sql` | NOT NULL nas FKs, CHECKs de domínio e `ON DELETE RESTRICT` em `order_items.product_id` |
| `002_alinha_schema.sql` | `locations.is_active` passa a `NOT NULL DEFAULT TRUE` (igual ao modelo) |

Para uma mudança nova:

1. Altere o `schema.sql` (bancos novos) **e** o modelo SQLAlchemy correspondente.
2. Crie `migrations/00N_descricao.sql` idempotente (bancos já existentes).
3. Rode `pytest` com `TEST_DATABASE_URL`: o `tests/test_schema_coerente.py` acusa qualquer diferença entre `schema.sql` e modelos.
4. Regenere o PDF: `python scripts/gerar_pdf_relacionamentos.py`.