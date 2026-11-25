# WarehouseFlow — Arquitetura DevOps

## Visão geral

Monorepositório com FastAPI (Jinja2 + HTML/CSS/JS), PostgreSQL 16 e Nginx como proxy reverso. A API serve a UI e a API REST; o Nginx é a porta de entrada HTTP.

```text
Browser  →  Nginx (frontend)  →  API (uvicorn :8000)  →  PostgreSQL 16
```

## Serviços

| Serviço | Imagem / build | Papel |
|---------|----------------|-------|
| `db` | `postgres:16-alpine` | Dados persistentes |
| `api` | `Dockerfile` (Python 3.12-slim) | FastAPI + Jinja2 + motor de otimização |
| `frontend` | Nginx Alpine (`deploy/Dockerfile.nginx` em prod) | Proxy reverso + headers de segurança |

## Ambientes

| Ambiente | Compose | Project name | Dados | Host típico |
|----------|---------|--------------|-------|-------------|
| Desenvolvimento | `docker-compose.yml` | default / `warehouseflow` | volume `warehouseflow_pgdata` | máquina local |
| Staging | `docker-compose.prod.yml` + `.env.staging` | `warehouseflow-staging` | volume `pgdata` do projeto | `/opt/warehouseflow/staging` |
| Produção | `docker-compose.prod.yml` + `.env.production` | `warehouseflow-production` | volume `pgdata` do projeto | `/opt/warehouseflow/production` |

Staging e produção **não compartilham** banco, volume, rede Compose nem arquivo `.env`.

## Diferenças Dev vs Prod

| Aspecto | Dev | Staging / Produção |
|---------|-----|--------------------|
| Código | Bind mounts `./backend`, `./frontend` | Incorporado na imagem |
| uvicorn | `--reload` via `command` no Compose | Sem `--reload` (CMD da imagem) |
| Porta API | `8000` publicada | Só rede interna Docker |
| Porta Postgres | `5433` publicada | Não publicada |
| Entrada HTTP | Nginx `8080` | Nginx `80` (ou `HTTP_PORT`) |
| Secrets | Fallback fraco de `SECRET_KEY` permitido | Sem fallback; chave forte obrigatória |

## Fluxo de branches

`feature/*` → `dev` → `staging` → `master`

Deploy operacional usa cópia do código em `/opt/warehouseflow/{staging,production}` e Compose com project names distintos. Não fazer merge automático nesta fase de documentação.

## Componentes de segurança (aplicação)

- JWT em cookie `access_token` (`HttpOnly`, `SameSite=Lax`, `Secure` via `COOKIE_SECURE`)
- RBAC existente (não alterado pela infra)
- `/docs` e `/openapi.json` controlados por `ENABLE_DOCS`
- Liveness: `GET /health`
- Readiness: `GET /ready` (ping real ao PostgreSQL)

## Documentos relacionados

- [docker.md](docker.md)
- [debian.md](debian.md)
- [deploy.md](deploy.md)
- [seguranca.md](seguranca.md)
- [backup.md](backup.md)
- [rollback.md](rollback.md)
