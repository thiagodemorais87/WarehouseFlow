-- database/seed.sql

-- 1. Roles
INSERT INTO roles (id, name) VALUES
(1, 'ADMIN'),
(2, 'OPERATOR'),
(3, 'MANAGER')
ON CONFLICT (id) DO NOTHING;

-- 2. Users (Senhas em hash simulado)
INSERT INTO users (id, name, email, password_hash, role_id) VALUES
(1, 'Carlos Admin', 'admin@warehouseflow.com', '$2b$12$eImiTXuWVxfM37uY4JANjO5E.86.Qj357', 1),
(2, 'João Operador', 'joao.operador@warehouseflow.com', '$2b$12$eImiTXuWVxfM37uY4JANjO5E.86.Qj357', 2)
ON CONFLICT (id) DO NOTHING;

-- 3. Warehouses
INSERT INTO warehouses (id, name, address) VALUES
(1, 'Armazém Central Recife', 'Av. Cais do Apolo, 100 - Recife, PE')
ON CONFLICT (id) DO NOTHING;

-- 4. Locations (Corredor - Estante - Prateleira)
INSERT INTO locations (id, warehouse_id, code, aisle, rack, shelf) VALUES
(1, 1, 'A1-01-A', 'A1', '01', 'A'),
(2, 1, 'A1-01-B', 'A1', '01', 'B'),
(3, 1, 'A1-02-A', 'A1', '02', 'A'),
(4, 1, 'B1-01-A', 'B1', '01', 'A'),
(5, 1, 'B1-01-B', 'B1', '01', 'B')
ON CONFLICT (id) DO NOTHING;

-- 5. Products
INSERT INTO products (id, sku, name, description, weight, volume) VALUES
(1, 'PROD-001', 'Monitor LED 24"', 'Monitor FHD 1080p para estações de trabalho', 3.50, 0.025),
(2, 'PROD-002', 'Teclado Mecânico RGB', 'Teclado mecânico switch blue N-Key Rollover', 0.95, 0.005),
(3, 'PROD-003', 'Cabo HDMI 2.0 2m', 'Cabo HDMI alta velocidade banhado a ouro', 0.15, 0.001)
ON CONFLICT (id) DO NOTHING;

-- 6. Stock
INSERT INTO stock (product_id, location_id, quantity) VALUES
(1, 1, 15), -- 15 Monitores na posição A1-01-A
(2, 2, 40), -- 40 Teclados na posição A1-01-B
(3, 3, 100) -- 100 Cabos na posição A1-02-A
ON CONFLICT DO NOTHING;

-- 7. Orders
INSERT INTO orders (id, type, status) VALUES
(1, 'OUTBOUND', 'PENDING'), -- Pedido de separação (Saída)
(2, 'INBOUND', 'COMPLETED') -- Recebimento (Entrada)
ON CONFLICT (id) DO NOTHING;

-- 8. Order Items
INSERT INTO order_items (order_id, product_id, quantity) VALUES
(1, 1, 2), -- Pedido 1 precisa de 2 Monitores
(1, 2, 1), -- Pedido 1 precisa de 1 Teclado
(2, 3, 50) -- Pedido 2 recebeu 50 Cabos
ON CONFLICT DO NOTHING;

-- 9. Tasks
INSERT INTO tasks (id, type, status, order_id, assigned_user_id) VALUES
(1, 'PICKING', 'PENDING', 1, 2) -- Tarefa de separação atribuída ao João Operador
ON CONFLICT (id) DO NOTHING;

-- 10. Optimization Results (Exemplo com Rota Sugerida em JSON)
INSERT INTO optimization_results (task_id, suggested_location_id, suggested_route, score) VALUES
(1, 1, '{"steps": ["A1-01-A", "A1-01-B"], "total_distance_meters": 12.5}', 0.9450)
ON CONFLICT DO NOTHING;

-- Ajustar a sequência dos IDS após as inserções manuais
SELECT setval('roles_id_seq', (SELECT MAX(id) FROM roles));
SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));
SELECT setval('warehouses_id_seq', (SELECT MAX(id) FROM warehouses));
SELECT setval('locations_id_seq', (SELECT MAX(id) FROM locations));
SELECT setval('products_id_seq', (SELECT MAX(id) FROM products));
SELECT setval('orders_id_seq', (SELECT MAX(id) FROM orders));
SELECT setval('tasks_id_seq', (SELECT MAX(id) FROM tasks));