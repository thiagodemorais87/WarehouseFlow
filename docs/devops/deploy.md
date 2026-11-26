# WarehouseFlow — Deploy

## Deploy automatizado (CI/CD)

O caminho padrão é o pipeline GitHub Actions: merge em `staging` implanta staging; merge em `master` implanta produção após aprovação. Imagens vêm do GHCR, o `.env` é gerado a partir dos GitHub Secrets e há health check com rollback automático. Configuração e operação: [ci-cd.md](ci-cd.md).

Os procedimentos abaixo continuam válidos para deploy manual (sem pipeline). Atenção: depois do primeiro deploy automatizado, o `.env.<ambiente>` do servidor passa a apontar para as imagens do GHCR (`API_IMAGE`, `NGINX_IMAGE`, `IMAGE_TAG`); um `up -d --build` manual reconstrói a partir do código local, mas com o nome de imagem do GHCR.

## Pré-requisitos

- Código no host em `/opt/warehouseflow/staging` ou `/opt/warehouseflow/production`
- Arquivo `.env.staging` ou `.env.production` preenchido (sem placeholders fracos)
- Docker Compose v2

## Staging

```bash
cd /opt/warehouseflow/staging
git pull
docker compose -p warehouseflow-staging --env-file .env.staging -f docker-compose.prod.yml up -d --build
docker compose -p warehouseflow-staging --env-file .env.staging -f docker-compose.prod.yml ps
curl -s http://127.0.0.1/health
curl -s http://127.0.0.1/ready
```

## Produção

```bash
cd /opt/warehouseflow/production
git pull
# Backup antes de mudanças relevantes — ver backup.md
docker compose -p warehouseflow-production --env-file .env.production -f docker-compose.prod.yml up -d --build
docker compose -p warehouseflow-production --env-file .env.production -f docker-compose.prod.yml ps
curl -s http://127.0.0.1/health
curl -s http://127.0.0.1/ready
```

## Migrations SQL (bancos já existentes)

`initdb.d` **não** reexecuta em volume já inicializado. Após o deploy, se houver scripts novos:

```bash
# Staging
cd /opt/warehouseflow/staging
set -a && source .env.staging && set +a
docker compose -p warehouseflow-staging --env-file .env.staging -f docker-compose.prod.yml \
  exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -f /migrations/001_constraints.sql
```

Repita para cada arquivo em `backend/database/migrations/` na ordem numérica. Detalhes: [`backend/database/README.md`](../../backend/database/README.md).

## Nginx e HTTPS (etapa própria)

HTTP inicial: `deploy/nginx.prod.conf` (embutido em `deploy/Dockerfile.nginx`), `server_name _`.

Para HTTPS:

1. Obter certificado (Certbot no host ou similar).
2. Usar [`deploy/nginx-ssl.conf.example`](../../deploy/nginx-ssl.conf.example) como base.
3. Remontar/rebuild da imagem Nginx com a conf SSL e publicar `443`.
4. Definir `COOKIE_SECURE=true` no `.env` do ambiente e recriar o serviço `api`:

```bash
docker compose -p warehouseflow-production --env-file .env.production -f docker-compose.prod.yml up -d api
```

## Validação funcional rápida

```bash
# Health / ready via Nginx
curl -i http://IP_OU_DOMINIO/health
curl -i http://IP_OU_DOMINIO/ready

# Login HTML (deve retornar cookie se COOKIE_SECURE=false em HTTP)
curl -i -X POST http://IP_OU_DOMINIO/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=admin@warehouseflow.com&password=admin123"
```

(Ajuste e-mail/senha conforme o seed do ambiente.)

## Logs

```bash
docker compose -p warehouseflow-staging --env-file .env.staging -f docker-compose.prod.yml logs -f --tail=100 api
docker compose -p warehouseflow-production --env-file .env.production -f docker-compose.prod.yml logs -f --tail=100 api
```
