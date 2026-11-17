# MER final — WarehouseFlow

Este diagrama foi reconstituído a partir de `backend/database/schema.sql`,
`backend/app/models/` e `backend/app/models/optimization_run.py`. É um modelo
do código; a verificação de uma instância PostgreSQL real ficou pendente por
indisponibilidade do daemon Docker.

```mermaid
erDiagram
    ROLES ||--o{ USERS : assigns
    WAREHOUSES ||--o{ LOCATIONS : contains
    PRODUCTS ||--o{ STOCK : stored_as
    LOCATIONS ||--o{ STOCK : holds
    ORDERS ||--o{ ORDER_ITEMS : contains
    PRODUCTS ||--o{ ORDER_ITEMS : ordered_as
    ORDERS ||--o{ TASKS : generates
    USERS o|--o{ TASKS : assigned_to
    TASKS ||--o{ OPTIMIZATION_RESULTS : records
    LOCATIONS o|--o{ OPTIMIZATION_RESULTS : suggested_at

    ROLES {
        int id PK
        string name UK
    }
    USERS {
        int id PK
        string name
        string email UK
        string password_hash
        int role_id FK
        bool is_active
        datetime created_at
    }
    PRODUCTS {
        int id PK
        string sku UK
        string name
        string description
        decimal weight
        decimal volume
    }
    WAREHOUSES {
        int id PK
        string name
        string address
    }
    LOCATIONS {
        int id PK
        int warehouse_id FK
        string code UK
        string aisle
        string rack
        string shelf
        bool is_active
    }
    STOCK {
        int id PK
        int product_id FK
        int location_id FK
        int quantity
        datetime last_updated
    }
    ORDERS {
        int id PK
        string type
        string status
        datetime created_at
    }
    ORDER_ITEMS {
        int id PK
        int order_id FK
        int product_id FK
        int quantity
    }
    TASKS {
        int id PK
        string type
        string status
        int order_id FK
        int assigned_user_id FK
        datetime created_at
    }
    OPTIMIZATION_RESULTS {
        int id PK
        int task_id FK
        int suggested_location_id FK
        json suggested_route
        decimal score
        datetime created_at
    }
    OPTIMIZATION_RUNS {
        int id PK
        int user_id
        string user_email
        datetime executed_at
        string source
        int order_id
        json original_route
        json nearest_neighbor_route
        json two_opt_route
        float distance_before
        float nearest_neighbor_distance
        float two_opt_distance
        float distance_after
        float distance_reduction
        float reduction_percent
        float execution_time_ms
        int locations_count
    }
```

`stock` tem restrição única em `(product_id, location_id)` e quantidade não
negativa; itens de pedido exigem quantidade positiva e preservam a referência
ao produto (`ON DELETE RESTRICT`). O pedido é pai de itens e tarefas; a remoção
do pedido é em cascata. `optimization_runs` é tabela adicional do modelo ORM:
`user_id` e `order_id` são valores de histórico, sem chaves estrangeiras
declaradas nessa tabela.

Inventário observado na base SQLite descartável, criada pela aplicação para
smoke tests: 11 tabelas e as FKs listadas em
[`evidencias/S10-database-schema.txt`](./evidencias/S10-database-schema.txt).
Esse artefato não é evidência de conexão PostgreSQL.
