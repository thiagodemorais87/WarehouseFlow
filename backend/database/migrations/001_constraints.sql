BEGIN;

-- 1) Pré-checagem: linhas órfãs impedem NOT NULL
DO $$
DECLARE n integer;
BEGIN
    SELECT count(*) INTO n FROM stock WHERE product_id IS NULL OR location_id IS NULL;
    IF n > 0 THEN RAISE EXCEPTION 'stock: % linha(s) sem product_id/location_id. Corrija antes de migrar.', n; END IF;
    SELECT count(*) INTO n FROM order_items WHERE order_id IS NULL OR product_id IS NULL;
    IF n > 0 THEN RAISE EXCEPTION 'order_items: % linha(s) sem order_id/product_id. Corrija antes de migrar.', n; END IF;
    SELECT count(*) INTO n FROM tasks WHERE order_id IS NULL;
    IF n > 0 THEN RAISE EXCEPTION 'tasks: % linha(s) sem order_id. Corrija antes de migrar.', n; END IF;
    SELECT count(*) INTO n FROM optimization_results WHERE task_id IS NULL;
    IF n > 0 THEN RAISE EXCEPTION 'optimization_results: % linha(s) sem task_id. Corrija antes de migrar.', n; END IF;
END $$;

-- 2) NOT NULL (ALTER é idempotente)
ALTER TABLE stock                ALTER COLUMN product_id  SET NOT NULL;
ALTER TABLE stock                ALTER COLUMN location_id SET NOT NULL;
ALTER TABLE order_items          ALTER COLUMN order_id    SET NOT NULL;
ALTER TABLE order_items          ALTER COLUMN product_id  SET NOT NULL;
ALTER TABLE tasks                ALTER COLUMN order_id    SET NOT NULL;
ALTER TABLE optimization_results ALTER COLUMN task_id     SET NOT NULL;

-- 3) CHECKs (só cria se ainda não existir)
DO $$
DECLARE c record;
BEGIN
    FOR c IN SELECT * FROM (VALUES
        ('products',    'ck_products_weight_non_negative',  'weight IS NULL OR weight >= 0'),
        ('products',    'ck_products_volume_non_negative',  'volume IS NULL OR volume >= 0'),
        ('stock',       'ck_stock_quantity_non_negative',   'quantity >= 0'),
        ('order_items', 'ck_order_items_quantity_positive', 'quantity > 0'),
        ('orders',      'ck_orders_type',   $q$type IN ('INBOUND', 'OUTBOUND')$q$),
        ('orders',      'ck_orders_status', $q$status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'CANCELLED')$q$),
        ('tasks',       'ck_tasks_type',    $q$type IN ('PICKING', 'PUTAWAY', 'REPLENISHMENT')$q$),
        ('tasks',       'ck_tasks_status',  $q$status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED')$q$)
    ) AS t(tbl, name, expr)
    LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = c.name) THEN
            EXECUTE format('ALTER TABLE %I ADD CONSTRAINT %I CHECK (%s)', c.tbl, c.name, c.expr);
        END IF;
    END LOOP;
END $$;

-- 4) order_items.product_id: ON DELETE RESTRICT
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_constraint
               WHERE conname = 'order_items_product_id_fkey' AND confdeltype <> 'r') THEN
        ALTER TABLE order_items DROP CONSTRAINT order_items_product_id_fkey;
        ALTER TABLE order_items ADD CONSTRAINT order_items_product_id_fkey
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT;
    END IF;
END $$;

COMMIT;