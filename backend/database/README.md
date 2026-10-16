# 🗄️ WarehouseFlow — Documentação do Banco de Dados

Esta pasta contém a modelagem, scripts DDL/DML e instruções de execução para o banco de dados relacional do **WarehouseFlow**, sistema inteligente de gerenciamento e otimização de operações em armazéns.

---

## 📁 Estrutura do Diretório

```text
backend/database/
├── schema.sql    # Script DDL: Criação das tabelas, chaves e relacionamentos
├── seed.sql      # Script DML: Dados iniciais de teste (massa de dados)
└── README.md     # Documentação do modelo de dados e instruções
```

---

## 📊 Modelo Entidade-Relacionamento (DER)

O banco foi projetado no **PostgreSQL** para suportar a gestão operacional de armazém e integrar com o motor de otimização de rotas e estocagem (*slotting*).

### Lista de Entidades e Tabelas

1. **`roles`**: Cargos e níveis de acesso dos usuários (ex: `ADMIN`, `OPERATOR`, `MANAGER`).
2. **`users`**: Cadastro de usuários/operadores do sistema.
3. **`warehouses`**: Armazéns ou depósitos físicos.
4. **`locations`**: Posições específicas dentro do armazém (Corredor, Estante, Prateleira).
5. **`products`**: Catálogo de produtos com dimensões (peso e volume para cálculo de otimização).
6. **`stock`**: Saldo de estoque por produto e por posição física.
7. **`orders`**: Pedidos de operação de entrada (`INBOUND`) ou saída (`OUTBOUND`).
8. **`order_items`**: Itens solicitados em cada pedido.
9. **`tasks`**: Tarefas operacionais vinculadas aos pedidos (ex: `PICKING`, `PUTAWAY`, `REPLENISHMENT`).
10. **`optimization_results`**: Resultados gerados pelo motor de otimização (rotas sugeridas em formato JSON, posições recomendadas e pontuação de eficiência).

---

## 📐 Dicionário de Dados

### 1. `roles`
| Coluna | Tipo | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PK | Identificador único |
| `name` | VARCHAR(50) | UNIQUE, NOT NULL | Nome do papel (ex: ADMIN, OPERATOR) |

### 2. `users`
| Coluna | Tipo | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PK | Identificador único |
| `name` | VARCHAR(100) | NOT NULL | Nome completo do usuário |
| `email` | VARCHAR(100) | UNIQUE, NOT NULL | E-mail do usuário |
| `password_hash` | VARCHAR(255) | NOT NULL | Senha criptografada |
| `role_id` | INTEGER | FK -> roles(id) | Papel/Cargo do usuário |
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
| `warehouse_id` | INTEGER | FK -> warehouses(id) | Armazém ao qual pertence |
| `code` | VARCHAR(20) | UNIQUE, NOT NULL | Código legível da posição (Ex: A1-05-B) |
| `aisle` | VARCHAR(10) | NULL | Corredor |
| `rack` | VARCHAR(10) | NULL | Estante / Prateleira vertical |
| `shelf` | VARCHAR(10) | NULL | Nível / Nivelamento |
| `is_active` | BOOLEAN | DEFAULT TRUE | Status de operação da posição |

### 6. `stock`
| Coluna | Tipo | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PK | Identificador único |
| `product_id` | INTEGER | FK -> products(id) | Produto em estoque |
| `location_id` | INTEGER | FK -> locations(id) | Posição no armazém |
| `quantity` | INTEGER | NOT NULL DEFAULT 0 | Quantidade disponível |
| `last_updated` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | ÚLtima atualização |
| *Constraint* | UNIQUE(product_id, location_id) | | Impede duplicidade do mesmo produto na mesma vaga |

### 7. `orders`
| Coluna | Tipo | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PK | Identificador único |
| `type` | VARCHAR(20) | NOT NULL | Tipo: `INBOUND` ou `OUTBOUND` |
| `status` | VARCHAR(20) | DEFAULT 'PENDING' | Status: `PENDING`, `PROCESSING`, `COMPLETED`, `CANCELLED` |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Data do pedido |

### 8. `order_items`
| Coluna | Tipo | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PK | Identificador único |
| `order_id` | INTEGER | FK -> orders(id) | Pedido associado |
| `product_id` | INTEGER | FK -> products(id) | Produto |
| `quantity` | INTEGER | NOT NULL | Quantidade solicitada |

### 9. `tasks`
| Coluna | Tipo | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PK | Identificador único |
| `type` | VARCHAR(30) | NOT NULL | Tipo de tarefa (`PICKING`, `PUTAWAY`, `REPLENISHMENT`) |
| `status` | VARCHAR(20) | DEFAULT 'PENDING' | Status (`PENDING`, `IN_PROGRESS`, `COMPLETED`) |
| `order_id` | INTEGER | FK -> orders(id) | Pedido origem |
| `assigned_user_id` | INTEGER | FK -> users(id) | Operador atribuído |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Data de criação |

### 10. `optimization_results`
| Coluna | Tipo | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PK | Identificador único |
| `task_id` | INTEGER | FK -> tasks(id) | Tarefa associada |
| `suggested_location_id` | INTEGER | FK -> locations(id) | Posição sugerida pelo algoritmo |
| `suggested_route` | JSONB | NULL | Sequência otimizada de passos/rotas em JSON |
| `score` | DECIMAL(10,4) | NULL | Métrica de eficiência / custo da solução |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Data de geração do cálculo |

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
Estando na raiz do projeto, rode o script para criar a estrutura completa de tabelas:

```bash
psql -U postgres -d warehouseflow -f backend/database/schema.sql
```

### 3. Popular com a Massa de Testes (`seed.sql`)
Execute o script DML para inserir os registros iniciais nas tabelas:

```bash
psql -U postgres -d warehouseflow -f backend/database/seed.sql
```

---

## Fluxo para Migrations Futuras (Sprint 02+)

Na Sprint 02, o versionamento do schema do banco será gerenciado via **Alembic** integrado ao **SQLAlchemy**, garantindo que alterações estruturais futuras sejam versionadas com segurança sem perda de dados.