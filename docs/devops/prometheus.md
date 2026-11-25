# WarehouseFlow — Prometheus + cAdvisor + exporters

Coleta de métricas em Docker, isolada da aplicação. UIs e scrapes administrativos **não** vão para a internet.

## Componentes

| Serviço | Imagem | Papel |
|---------|--------|-------|
| `prometheus` | `prom/prometheus:v2.55.1` | TSDB + scrape |
| `cadvisor` | `gcr.io/cadvisor/cadvisor:v0.49.1` | CPU/mem/rede/estado por container |
| `node-exporter` | `prom/node-exporter:v1.8.2` | Métricas do host (via mounts) |
| `postgres-exporter` | `prometheuscommunity/postgres-exporter:v0.16.0` | Métricas do Postgres **da app** |
| `blackbox-exporter` | `prom/blackbox-exporter:v0.25.0` | Probes HTTP `/health` e `/ready` |

Configs: [`monitoring/prometheus/`](../../monitoring/prometheus/)

## Portas

| Serviço | Bind |
|---------|------|
| Prometheus UI | `127.0.0.1:9090` |
| cAdvisor / exporters | **sem publish** (só rede `monitoring` / `app`) |

Túnel SSH: `ssh -L 9090:127.0.0.1:9090 user@debian-host`

## Volumes

- `warehouseflow-monitoring_prometheus_data` — TSDB (retenção **15d**)

## Jobs de scrape

Definidos em [`monitoring/prometheus/prometheus.yml`](../../monitoring/prometheus/prometheus.yml):

| Job | Target |
|-----|--------|
| `prometheus` | `localhost:9090` |
| `cadvisor` | `cadvisor:8080` |
| `node` | `node-exporter:9100` |
| `postgres` | `postgres-exporter:9187` |
| `blackbox` | `blackbox-exporter:9115` |
| `warehouseflow-health` | probe `http://frontend/health` |
| `warehouseflow-ready` | probe `http://frontend/ready` |

**Não declarar coleta OK sem verificar targets UP.**

```bash
curl -s http://127.0.0.1:9090/api/v1/targets | python3 -m json.tool
# Ou UI: Status → Targets
curl -s http://127.0.0.1:9090/-/healthy
```

## Rede da aplicação

O Compose anexa Prometheus, postgres-exporter e blackbox à rede externa `APP_NETWORK` (ex. `warehouseflow_default`) para resolver `frontend` e `db`.

```bash
docker network ls
# Ajuste APP_NETWORK em .env.monitoring
```

## Usuário read-only no Postgres da app

No banco **WarehouseFlow** (não no `zabbix-db`):

```sql
CREATE ROLE monitoring WITH LOGIN PASSWORD 'senha_forte';
GRANT CONNECT ON DATABASE warehouseflow TO monitoring;
GRANT USAGE ON SCHEMA public TO monitoring;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitoring;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO monitoring;
-- Para pg_stat_* o exporter usa views/funções; em PG 16 costuma bastar CONNECT + privilégios padrão do exporter.
-- Alternativa simples em lab: conceder pg_monitor
GRANT pg_monitor TO monitoring;
```

DSN em `.env.monitoring`:

```env
POSTGRES_EXPORTER_DSN=postgresql://monitoring:senha_forte@db:5432/warehouseflow?sslmode=disable
```

## cAdvisor — mounts do host

| Host | Container | Modo |
|------|-----------|------|
| `/` | `/rootfs` | ro |
| `/var/run` | `/var/run` | ro (docker.sock) |
| `/sys` | `/sys` | ro |
| `/var/lib/docker/` | `/var/lib/docker` | ro |

Flags: `--docker_only=true`, housekeeping 30s. O Compose usa `privileged: true` + `/dev/kmsg` + mount explícito de `docker.sock` porque, sem isso, o cAdvisor costuma listar containers via API Docker mas falha ao ler layerdb/cgroups (`Failed to create existing container` / séries só com `id="/"`).

Em Debian/EC2 nativo, se a coleta por container funcionar sem privileged, remova `privileged` e `devices` e mantenha apenas os mounts ro. Em Docker Desktop (Windows/macOS) o privileged costuma ser inevitável; valide de novo na VM Debian antes de endurecer.

Validar métricas por container:

```bash
curl -s 'http://127.0.0.1:9090/api/v1/query?query=count(container_memory_working_set_bytes{id!="/"})'
```

## node-exporter

Roda com `pid: host` e rootfs montado em `/host` para métricas do SO. Em Docker Desktop (Windows/macOS) as métricas refletem a VM Linux embutida, não o Windows nativo — no Debian/EC2 refletem o host real.

No Debian, se o mount `/: /host:ro` falhar por causa de propagation, use `/: /host:ro,rslave` (o Compose atual omite `rslave` para compatibilidade com Docker Desktop).

## Alertas

[`monitoring/prometheus/alerts.yml`](../../monitoring/prometheus/alerts.yml): TargetDown, health/ready falhando, memória alta, disco quase cheio. Avaliação no próprio Prometheus (sem Alertmanager neste desenho).

## Inicialização e recuperação

```bash
docker compose -p warehouseflow-monitoring \
  -f docker-compose.monitoring.yml --env-file .env.monitoring up -d

# Recarregar config sem downtime (lifecycle habilitado)
curl -X POST http://127.0.0.1:9090/-/reload
```

Sob pressão de memória, desligar primeiro: Grafana + Prometheus + exporters + cAdvisor (a app continua). Ver também [zabbix.md](zabbix.md).
