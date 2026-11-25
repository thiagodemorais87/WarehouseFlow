# WarehouseFlow — Backup e restauração PostgreSQL

Use sempre `pg_dump` / `pg_restore` (ou `psql`) a partir do container. **Não** copie o diretório de dados (`pgdata`) com o PostgreSQL em execução — isso gera backup inconsistente.

**Não** apague volumes para “fazer backup”.

## Backup (custom format)

### Desenvolvimento

```bash
mkdir -p backups
docker compose exec -T db pg_dump -U warehouse -d warehouseflow -Fc -f /tmp/warehouseflow.dump
docker compose cp db:/tmp/warehouseflow.dump "./backups/warehouseflow-$(date +%Y%m%d-%H%M%S).dump"
```

No PowerShell (Windows), ajuste a data:

```powershell
New-Item -ItemType Directory -Force -Path backups | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
docker compose exec -T db pg_dump -U warehouse -d warehouseflow -Fc -f /tmp/warehouseflow.dump
docker compose cp "db:/tmp/warehouseflow.dump" "backups/warehouseflow-$stamp.dump"
```

### Staging

```bash
cd /opt/warehouseflow/staging
mkdir -p backups
set -a && source .env.staging && set +a
docker compose -p warehouseflow-staging --env-file .env.staging -f docker-compose.prod.yml \
  exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/wf.dump
docker compose -p warehouseflow-staging --env-file .env.staging -f docker-compose.prod.yml \
  cp db:/tmp/wf.dump "./backups/staging-$(date +%Y%m%d-%H%M%S).dump"
```

### Produção

```bash
cd /opt/warehouseflow/production
mkdir -p backups
set -a && source .env.production && set +a
docker compose -p warehouseflow-production --env-file .env.production -f docker-compose.prod.yml \
  exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/wf.dump
docker compose -p warehouseflow-production --env-file .env.production -f docker-compose.prod.yml \
  cp db:/tmp/wf.dump "./backups/production-$(date +%Y%m%d-%H%M%S).dump"
```

Guarde os dumps fora do servidor quando possível (S3, outro disco, etc.).

## Restauração (custom format)

Atenção: restauração sobrescreve/altera dados. Em produção, confirme o arquivo e faça um dump novo antes.

```bash
# Exemplo staging
cd /opt/warehouseflow/staging
set -a && source .env.staging && set +a
docker compose -p warehouseflow-staging --env-file .env.staging -f docker-compose.prod.yml \
  cp ./backups/SEU_ARQUIVO.dump db:/tmp/restore.dump
docker compose -p warehouseflow-staging --env-file .env.staging -f docker-compose.prod.yml \
  exec -T db pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists /tmp/restore.dump
```

Flags `--clean --if-exists` removem objetos antes de recriar. Use com cuidado. Alternativa mais conservadora: restaurar em um banco novo e validar.

## SQL plain (alternativa)

```bash
docker compose exec -T db pg_dump -U warehouse -d warehouseflow > backups/warehouseflow.sql
docker compose exec -T db psql -U warehouse -d warehouseflow < backups/warehouseflow.sql
```

## Persistência de volume

O volume Docker (`warehouseflow_pgdata` em dev; `pgdata` scoped ao project name em staging/prod) sobrevive a `docker compose down` **sem** `-v`.

Nunca use `docker compose down -v` em staging/produção a menos que a exclusão dos dados seja intencional e documentada.
