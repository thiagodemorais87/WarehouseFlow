# WarehouseFlow — Segurança operacional

## Variáveis críticas

| Variável | Dev | Staging / Produção |
|----------|-----|--------------------|
| `SECRET_KEY` | Obrigatória; Compose pode usar fallback fraco só em dev | Obrigatória, ≥ 32 chars, sem placeholders; app falha ao subir se fraca |
| `COOKIE_SECURE` | `false` (HTTP) | `false` até HTTPS; depois `true` |
| `ENABLE_DOCS` | `true` | Preferir `false` |
| `APP_ENV` | `development` | `staging` ou `production` |
| `POSTGRES_PASSWORD` | fixo local (`warehouse`) | Senha forte, única por ambiente |
| `DATABASE_URL` | sobrescrita no Compose dev | Deve bater com `POSTGRES_*` |

Nunca commite `.env`, `.env.staging` ou `.env.production` com secrets reais. Use apenas os `*.example`.

## Cookie JWT

- Nome: `access_token`
- `HttpOnly=true`
- `SameSite=Lax`
- `Secure` controlado por `COOKIE_SECURE` (default `false`)

Ative `COOKIE_SECURE=true` **somente** depois que o site for servido em HTTPS; caso contrário o navegador não envia o cookie e o login HTML quebra.

## Superfície de rede

| Porta | Dev | Staging / Prod |
|-------|-----|----------------|
| Nginx 80 (ou `HTTP_PORT`) | `8080` no host | Publicada |
| API 8000 | Publicada (debug) | **Não** publicada |
| Postgres 5432 | `5433` no host | **Não** publicada |

A API só deve ser acessível pela rede Docker interna (`http://api:8000`), via Nginx.

## OpenAPI / Swagger

Com `ENABLE_DOCS=false`:

- `/docs` → 404
- `/redoc` → 404
- `/openapi.json` → 404

## Headers Nginx

Configurados em `deploy/nginx.conf` (dev) e `deploy/nginx.prod.conf` (prod):

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: SAMEORIGIN`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `X-XSS-Protection: 0` (desativa heurística legada; preferir CSP em etapas futuras)
- Encaminhamento: `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto`

## O que esta fase não altera

- Regras de autenticação/autorização (RBAC)
- Algoritmo JWT (HS256) nem tempo de expiração
- Modelo de dados ou regras de negócio

## Checklist rápido pré-deploy

1. `SECRET_KEY` longa e única
2. Senhas Postgres distintas entre staging e produção
3. `ENABLE_DOCS=false` (salvo necessidade temporária)
4. Security group / firewall sem 5432/8000 públicos
5. Após TLS: `COOKIE_SECURE=true` + conf SSL
