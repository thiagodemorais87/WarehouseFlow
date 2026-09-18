-- 1. Roles (Cargos/Papéis)
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

-- 2. Users (Usuários/Operadores)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id INTEGER REFERENCES roles(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Products (Produtos)
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    weight DECIMAL(10,2), -- em kg
    volume DECIMAL(10,2)  -- em m3 ou cm3
);

-- 4. Warehouses (Armazéns)
CREATE TABLE warehouses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address TEXT
);

-- 5. Locations (Posições no armazém: Corredor, Estante, Prateleira)
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    warehouse_id INTEGER REFERENCES warehouses(id) ON DELETE CASCADE,
    code VARCHAR(20) UNIQUE NOT NULL, -- Ex: A1-05-B
    aisle VARCHAR(10),
    rack VARCHAR(10),
    shelf VARCHAR(10),
    is_active BOOLEAN DEFAULT TRUE
);

-- 6. Stock (Estoque)
CREATE TABLE stock (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    location_id INTEGER REFERENCES locations(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, location_id)
);

-- 7. Orders (Pedidos de Entrada/Saída)
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    type VARCHAR(20) NOT NULL, -- INBOUND (Recebimento) ou OUTBOUND (Expedição)
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Order Items (Itens do Pedido)
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL
);

-- 9. Tasks (Tarefas Operacionais: Separação, Movimentação)
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    type VARCHAR(30) NOT NULL, -- PICKING, PUTAWAY, REPLENISHMENT
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    assigned_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. Optimization Results (Resultados do Motor de Otimização)
CREATE TABLE optimization_results (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    suggested_location_id INTEGER REFERENCES locations(id),
    suggested_route JSONB, -- Rota sugerida armazenada em formato JSON
    score DECIMAL(10,4), -- Pontuação/Custo calculado pelo algoritmo
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);