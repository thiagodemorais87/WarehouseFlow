# WarehouseFlow — Rollback

## Princípios

1. Preferir redeploy de uma revisão Git / tag de imagem conhecida como boa.
2. Se o problema for de dados, restaurar dump (`backup.md`) **depois** de voltar a aplicação estável.
3. Não usar `docker compose down -v` como “rollback”.
4. Não fazer `git push --force` nem reescrever histórico compartilhado.

## Rollback de aplicação (staging)

```bash
cd /opt/warehouseflow/staging
git fetch
git checkout <COMMIT_OU_TAG_BOA>
docker compose -p warehouseflow-staging --env-file .env.staging -f docker-compose.prod.yml up -d --build
curl -s http://127.0.0.1/health
curl -s http://127.0.0.1/ready
```

## Rollback de aplicação (produção)

```bash
cd /opt/warehouseflow/production
git fetch
git checkout <COMMIT_OU_TAG_BOA>
docker compose -p warehouseflow-production --env-file .env.production -f docker-compose.prod.yml up -d --build
curl -s http://127.0.0.1/health
curl -s http://127.0.0.1/ready
```

Se as imagens forem tagueadas por `APP_VERSION`, você também pode redefinir `APP_VERSION` no `.env` para a tag anterior e rebuildar/recriar os serviços.

## Rollback de dados

1. Pare escritas críticas se necessário (manutenção).
2. Restaure o dump conforme [backup.md](backup.md).
3. Valide `/ready`, login e um fluxo CRUD simples.

## Rollback só do Nginx

Se a conf SSL/HTTP quebrar a entrada, volte a imagem Nginx anterior ou restaure `deploy/nginx.prod.conf` conhecido e rebuild:

```bash
docker compose -p warehouseflow-production --env-file .env.production -f docker-compose.prod.yml \
  up -d --build frontend
```

## Checklist pós-rollback

- [ ] `GET /health` → `{"status":"ok",...}`
- [ ] `GET /ready` → `{"status":"ready"}`
- [ ] Login funciona (atenção a `COOKIE_SECURE` vs HTTP/HTTPS)
- [ ] Logs da API sem traceback contínuo
- [ ] Volume Postgres intacto (`docker volume ls` | grep warehouseflow)
