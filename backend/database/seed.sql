-- database/seed.sql
-- Dados de demonstração DETERMINÍSTICOS (ids e datas fixos) e idempotentes
-- (ON CONFLICT em todos os INSERTs): rodar de novo não duplica nada.
--
-- Cobre o que o dashboard e os relatórios da Sprint 07 mostram:
--   pedidos em todos os status e tipos, tarefas em vários status, 2 itens com
--   estoque baixo (<= 10) e 3 execuções do motor de otimização (relatório de picking).
-- Requer o schema.sql aplicado antes (docker-entrypoint-initdb.d/01-schema.sql).

-- 1. Roles
INSERT INTO roles (id, name) VALUES
(1, 'ADMIN'),
(2, 'OPERADOR'),
(3, 'GESTOR')
ON CONFLICT (id) DO NOTHING;

-- 2. Users (senha de demo para todos: admin123)
INSERT INTO users (id, name, email, password_hash, role_id, is_active) VALUES
(1, 'Carlos Admin', 'admin@warehouseflow.com', '$2b$12$i/tln6nI/fn1EN/kl6O21eD9JvZCdWlqrTGARYsLdD4kXQExA9vxu', 1, TRUE),
(2, 'João Operador', 'joao.operador@warehouseflow.com', '$2b$12$i/tln6nI/fn1EN/kl6O21eD9JvZCdWlqrTGARYsLdD4kXQExA9vxu', 2, TRUE),
(3, 'Maria Gestora', 'maria.gestora@warehouseflow.com', '$2b$12$i/tln6nI/fn1EN/kl6O21eD9JvZCdWlqrTGARYsLdD4kXQExA9vxu', 3, TRUE)
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
(3, 'PROD-003', 'Cabo HDMI 2.0 2m', 'Cabo HDMI alta velocidade banhado a ouro', 0.15, 0.001),
(4, 'PROD-004', 'Mouse Óptico USB', 'Mouse óptico 1200 DPI com fio', 0.10, 0.0008),
(5, 'PROD-005', 'Headset Gamer 7.1', 'Headset USB com microfone e som surround virtual', 0.45, 0.004)
ON CONFLICT (id) DO NOTHING;

-- 6. Stock
INSERT INTO stock (id, product_id, location_id, quantity) VALUES
(1, 1, 1, 15), -- 15 Monitores na posição A1-01-A
(2, 2, 2, 40), -- 40 Teclados na posição A1-01-B
(3, 3, 3, 100), -- 100 Cabos na posição A1-02-A
(4, 4, 4, 6),   -- 6 Mouses na posição B1-01-A  (estoque baixo)
(5, 5, 5, 3)    -- 3 Headsets na posição B1-01-B (estoque baixo)
ON CONFLICT (id) DO NOTHING;

-- 7. Orders
-- created_at fixo: os filtros de período dos relatórios dão sempre o mesmo resultado
INSERT INTO orders (id, type, status, created_at) VALUES
(1, 'OUTBOUND', 'PENDING',    '2026-10-26 09:00:00'), -- Pedido de separação (Saída)
(2, 'INBOUND',  'COMPLETED',  '2026-10-20 14:30:00'), -- Recebimento (Entrada)
(3, 'OUTBOUND', 'PROCESSING', '2026-10-27 10:15:00'), -- Separação em andamento
(4, 'OUTBOUND', 'COMPLETED',  '2026-10-22 16:45:00'), -- Saída concluída
(5, 'INBOUND',  'PENDING',    '2026-10-28 08:00:00'), -- Recebimento aguardando armazenagem
(6, 'OUTBOUND', 'CANCELLED',  '2026-10-18 11:20:00')  -- Pedido cancelado
ON CONFLICT (id) DO NOTHING;

-- 8. Order Items
INSERT INTO order_items (id, order_id, product_id, quantity) VALUES
(1, 1, 1, 2),  -- Pedido 1 precisa de 2 Monitores
(2, 1, 2, 1),  -- Pedido 1 precisa de 1 Teclado
(3, 2, 3, 50), -- Pedido 2 recebeu 50 Cabos
(4, 3, 2, 5),  -- Pedido 3 separa 5 Teclados
(5, 3, 4, 2),  -- Pedido 3 separa 2 Mouses
(6, 4, 1, 3),  -- Pedido 4 saiu com 3 Monitores
(7, 5, 4, 20), -- Pedido 5 vai receber 20 Mouses
(8, 5, 5, 10), -- Pedido 5 vai receber 10 Headsets
(9, 6, 3, 8)   -- Pedido 6 (cancelado) pedia 8 Cabos
ON CONFLICT (id) DO NOTHING;

-- 9. Tasks
INSERT INTO tasks (id, type, status, order_id, assigned_user_id, created_at) VALUES
(1, 'PICKING', 'PENDING',     1, 2,    '2026-10-26 09:05:00'), -- Separação atribuída ao João Operador
(2, 'PICKING', 'IN_PROGRESS', 3, 2,    '2026-10-27 10:20:00'), -- Separação em andamento (João)
(3, 'PICKING', 'COMPLETED',   4, 2,    '2026-10-22 16:50:00'), -- Separação concluída (João)
(4, 'PUTAWAY', 'PENDING',     5, NULL, '2026-10-28 08:05:00')  -- Armazenagem ainda sem responsável
ON CONFLICT (id) DO NOTHING;

-- 10. Optimization Results (Exemplo com Rota Sugerida em JSON)
INSERT INTO optimization_results (id, task_id, suggested_location_id, suggested_route, score) VALUES
(1, 1, 1, '{"steps": ["A1-01-A", "A1-01-B"], "total_distance_meters": 12.5}', 0.9450)
ON CONFLICT (id) DO NOTHING;

-- 11. Optimization Runs (histórico do motor NN + 2-opt; alimenta dashboard e relatório de picking)
-- Rotas = códigos das posições. distance_reduction = before - after; reduction_percent = reduction / before * 100.
INSERT INTO optimization_runs (
    id, user_id, user_email, executed_at, source, order_id,
    original_route, nearest_neighbor_route, two_opt_route,
    distance_before, nearest_neighbor_distance, two_opt_distance, distance_after,
    distance_reduction, reduction_percent, execution_time_ms, locations_count
) VALUES
(1, 2, 'joao.operador@warehouseflow.com', '2026-10-26 09:10:00', 'by-order', 1,
 '["A1-01-A", "B1-01-A", "A1-01-B"]',
 '["A1-01-A", "A1-01-B", "B1-01-A"]',
 '["A1-01-A", "A1-01-B", "B1-01-A"]',
 40.0, 32.0, 30.0, 30.0, 10.0, 25.0, 0.8, 3),
(2, 3, 'maria.gestora@warehouseflow.com', '2026-10-27 15:30:00', 'route', NULL,
 '["B1-01-B", "A1-01-A", "A1-02-A", "B1-01-A"]',
 '["B1-01-B", "B1-01-A", "A1-02-A", "A1-01-A"]',
 '["B1-01-B", "B1-01-A", "A1-01-A", "A1-02-A"]',
 50.0, 44.0, 40.0, 40.0, 10.0, 20.0, 1.2, 4),
(3, 1, 'admin@warehouseflow.com', '2026-10-28 09:00:00', 'by-order', 3,
 '["A1-02-A", "B1-01-B", "A1-01-A", "B1-01-A", "A1-01-B"]',
 '["A1-02-A", "A1-01-A", "A1-01-B", "B1-01-A", "B1-01-B"]',
 '["A1-02-A", "A1-01-A", "A1-01-B", "B1-01-A", "B1-01-B"]',
 80.0, 62.0, 56.0, 56.0, 24.0, 30.0, 2.1, 5)
ON CONFLICT (id) DO NOTHING;

-- Ajustar a sequência dos IDs de TODAS as tabelas após as inserções manuais
SELECT setval('roles_id_seq', (SELECT MAX(id) FROM roles));
SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));
SELECT setval('warehouses_id_seq', (SELECT MAX(id) FROM warehouses));
SELECT setval('locations_id_seq', (SELECT MAX(id) FROM locations));
SELECT setval('products_id_seq', (SELECT MAX(id) FROM products));
SELECT setval('stock_id_seq', (SELECT MAX(id) FROM stock));
SELECT setval('orders_id_seq', (SELECT MAX(id) FROM orders));
SELECT setval('order_items_id_seq', (SELECT MAX(id) FROM order_items));
SELECT setval('tasks_id_seq', (SELECT MAX(id) FROM tasks));
SELECT setval('optimization_results_id_seq', (SELECT MAX(id) FROM optimization_results));
SELECT setval('optimization_runs_id_seq', (SELECT MAX(id) FROM optimization_runs));