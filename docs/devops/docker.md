# WarehouseFlow — Docker

## Arquivos

| Arquivo | Uso |
|---------|-----|
| `Dockerfile` | Imagem da API (Python 3.12, usuário não-root, sem `--reload`) |
| `deploy/Dockerfile.nginx` | Imagem Nginx com `nginx.prod.conf` embutido |
| `docker-compose.yml` | Desenvolvimento local |
| `docker-compose.prod.yml` | Staging e produção |
| `.dockerignore` | Exclui `.env*`, testes, docs, venv do contexto de build |

## Desenvolvimento local

Pré-requisitos: Docker Desktop (ou Engine) + Compose v2.

```bash
cp .env.example .env
# Edite SECRET_KEY e, se necessário, outras variáveis

docker compose config
docker compose up --build -d
```

URLs locais:

- UI / proxy: http://localhost:8080
- API direta: http://localhost:8000
- Postgres host: `localhost:5433` (usuário/senha/db: `warehouse` / `warehouse` / `warehouseflow`)

Health:

```bash
curl -s http://localhost:8000/health
curl -s http://localhost:8000/ready
curl -s http://localhost:8080/health
```

Parar (mantém volume):

```bash
docker compose down
```

## Staging / produção (mesmo arquivo Compose)

```bash
# Staging
docker compose -p warehouseflow-staging --env-file .env.staging -f docker-compose.prod.yml config
docker compose -p warehouseflow-staging --env-file .env.staging -f docker-compose.prod.yml up -d --build

# Produção
docker compose -p warehouseflow-production --env-file .env.production -f docker-compose.prod.yml config
docker compose -p warehouseflow-production --env-file .env.production -f docker-compose.prod.yml up -d --build
```

Em produção/staging:

- Não há bind mount de código
- PostgreSQL **não** publica porta no host
- API **não** publica `8000` — acesso apenas via Nginx
- Volume de dados: `pgdata` (escopo do project name Compose)

## Build da API

```bash
docker build -t warehouseflow-api:dev --build-arg APP_VERSION=dev .
```

A imagem inclui `cython` via `requirements.txt`. A extensão nativa do motor (`optimization._native`) **não** é compilada no build da imagem (evita toolchain C). O fallback Python do motor permanece ativo. Build nativo opcional no host/container de desenvolvimento:

```bash
python backend/build_optimization_native.py
```

## Healthchecks

- `db`: `pg_isready`
- `api`: HTTP `GET /ready` (conectividade PostgreSQL)
- `frontend` (prod): espera `api` saudável (`condition: service_healthy`)

## Validação rápida de Compose

```bash
docker compose -f docker-compose.yml config
docker compose -f docker-compose.prod.yml --env-file .env.staging.example config
```
