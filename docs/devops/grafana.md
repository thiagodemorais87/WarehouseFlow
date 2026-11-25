# WarehouseFlow — Grafana

Dashboards provisionados sobre Prometheus. Autenticação obrigatória; UI só em localhost / túnel SSH.

## Componente

| Item | Valor |
|------|-------|
| Imagem | `grafana/grafana:11.3.1` |
| Porta | `127.0.0.1:3000` |
| Volume | `warehouseflow-monitoring_grafana_data` |
| Datasource | Prometheus → `http://prometheus:9090` (provisionado) |

Arquivos:

- [`monitoring/grafana/provisioning/`](../../monitoring/grafana/provisioning/)
- [`monitoring/grafana/dashboards/`](../../monitoring/grafana/dashboards/)

## Acesso

```bash
# Local
http://127.0.0.1:3000

# Túnel
ssh -L 3000:127.0.0.1:3000 user@debian-host
```

Credenciais via `.env.monitoring`:

- `GF_SECURITY_ADMIN_USER` (default `admin`)
- `GF_SECURITY_ADMIN_PASSWORD` (**obrigatório**, sem anônimo / sem sign-up)

Troque a senha após o primeiro login em produção.

## Dashboards

Pasta **WarehouseFlow** (auto-provisionada):

| Dashboard | UID | Métricas |
|-----------|-----|----------|
| Host Debian | `wf-host-debian` | `node_*` |
| Containers Docker | `wf-containers-docker` | `container_*` (cAdvisor) |
| WarehouseFlow | `wf-warehouseflow` | probes blackbox + containers da app |
| PostgreSQL | `wf-postgresql` | `pg_*` (postgres-exporter) |
| Monitoramento | `wf-monitoramento` | `up`, uso dos containers da stack |

Só usam séries existentes nos exporters/probes. Se um painel estiver vazio, verifique o target correspondente em Prometheus antes de alterar o JSON.

## Healthcheck

```bash
curl -s http://127.0.0.1:3000/api/health
# Esperado: {"database":"ok", ...}
```

Validar datasource: **Connections → Data sources → Prometheus → Save & test** → *Successfully queried the Prometheus API*.

## Inicialização

Sobe junto com o stack:

```bash
docker compose -p warehouseflow-monitoring \
  -f docker-compose.monitoring.yml --env-file .env.monitoring up -d grafana
```

Dashboards são montados read-only; edições na UI podem ser sobrescritas no restart se `allowUiUpdates` / provider assim definir. Preferir editar os JSON em `monitoring/grafana/dashboards/` e recriar o container.

## Recuperação

```bash
# Reinício preservando preferências no volume grafana_data
docker compose -p warehouseflow-monitoring -f docker-compose.monitoring.yml restart grafana

# Reset completo do Grafana (apaga preferências locais; dashboards voltam do provisionamento)
docker compose -p warehouseflow-monitoring -f docker-compose.monitoring.yml stop grafana
docker volume rm warehouseflow-monitoring_grafana_data
docker compose -p warehouseflow-monitoring -f docker-compose.monitoring.yml --env-file .env.monitoring up -d grafana
```

## Segurança

- Não publicar `3000` em `0.0.0.0` nem no Security Group da EC2.
- Não habilitar anonymous auth.
- Em pressão de memória, Grafana é um dos primeiros serviços a desligar (após ou junto com Prometheus/exporters). Ver [prometheus.md](prometheus.md) e [zabbix.md](zabbix.md).
