-- 002_alinha_schema.sql
-- Alinha bancos EXISTENTES com o schema.sql final (coerência com os modelos):
--   locations.is_active passa a ser NOT NULL DEFAULT TRUE (o modelo já exigia).
--
-- A tabela optimization_runs NÃO precisa de migration: a API a cria sozinha
-- na inicialização (Base.metadata.create_all) e o schema.sql a cria em bancos novos.
-- Se quiser criá-la manualmente: psql -f backend/database/optimization_runs.sql
--
-- Idempotente. Uso:
--   docker compose exec -T db psql -U warehouse -d warehouseflow -v ON_ERROR_STOP=1 \
--       -f /migrations/002_alinha_schema.sql

BEGIN;

-- posições antigas sem valor passam a ser ativas (era o DEFAULT da coluna)
UPDATE locations SET is_active = TRUE WHERE is_active IS NULL;

ALTER TABLE locations ALTER COLUMN is_active SET DEFAULT TRUE;
ALTER TABLE locations ALTER COLUMN is_active SET NOT NULL;

COMMIT;