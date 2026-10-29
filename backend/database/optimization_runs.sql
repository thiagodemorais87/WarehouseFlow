-- Histórico das execuções do motor de otimização (Sprint 07 / Thiago).
-- Artefato dedicado: não altera tabelas de outras pessoas.
-- Aplicar no Postgres após o schema base, ou deixar o ORM criar via Base.metadata.create_all.

CREATE TABLE IF NOT EXISTS optimization_runs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    user_email VARCHAR(100) NOT NULL,
    executed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(20) NOT NULL,
    order_id INTEGER NULL,
    original_route JSONB NOT NULL,
    nearest_neighbor_route JSONB NOT NULL,
    two_opt_route JSONB NOT NULL,
    distance_before DOUBLE PRECISION NOT NULL,
    nearest_neighbor_distance DOUBLE PRECISION NOT NULL,
    two_opt_distance DOUBLE PRECISION NOT NULL,
    distance_after DOUBLE PRECISION NOT NULL,
    distance_reduction DOUBLE PRECISION NOT NULL,
    reduction_percent DOUBLE PRECISION NOT NULL,
    execution_time_ms DOUBLE PRECISION NOT NULL,
    locations_count INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_optimization_runs_id ON optimization_runs (id);
CREATE INDEX IF NOT EXISTS ix_optimization_runs_executed_at ON optimization_runs (executed_at DESC);
