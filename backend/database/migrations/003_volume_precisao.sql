-- 003_volume_precisao.sql
-- products.volume era NUMERIC(10,2): volumes pequenos do seed (0.0008, 0.004 m³)
-- eram gravados como 0.00. Passa a NUMERIC(10,4), igual ao schema.sql/modelo.
-- Idempotente: só altera se a escala atual for diferente de 4.
BEGIN;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'products' AND column_name = 'volume'
          AND numeric_scale IS DISTINCT FROM 4
    ) THEN
        ALTER TABLE products ALTER COLUMN volume TYPE NUMERIC(10,4);
        -- recupera os valores de demo que foram truncados (apenas se ainda estiverem zerados)
        UPDATE products SET volume = v.volume
        FROM (VALUES ('PROD-003', 0.001), ('PROD-004', 0.0008), ('PROD-005', 0.004),
                     ('PROD-001', 0.025), ('PROD-002', 0.005)) AS v(sku, volume)
        WHERE products.sku = v.sku AND products.volume IN (0.00, 0.01, 0.03);
    END IF;
END $$;

COMMIT;
