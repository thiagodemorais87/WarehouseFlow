# WarehouseFlow — Zabbix (híbrido)

Zabbix Server + Web + PostgreSQL exclusivo em Docker. **Zabbix Agent 2 no host Debian** (métricas do SO real). Não misturar com o PostgreSQL do WarehouseFlow.

## Componentes

| Componente | Onde | Imagem / pacote |
|------------|------|-----------------|
| `zabbix-db` | Docker | `postgres:16.6-alpine` (DB `zabbix`) |
| `zabbix-server` | Docker | `zabbix/zabbix-server-pgsql:alpine-7.0.17` |
| `zabbix-web` | Docker | `zabbix/zabbix-web-nginx-pgsql:alpine-7.0.17` |
| Agent 2 | Host Debian | pacote `zabbix-agent2` 7.0.x |

Compose: [`docker-compose.monitoring.yml`](../../docker-compose.monitoring.yml)  
Env: [`.env.monitoring.example`](../../.env.monitoring.example)  
Agent exemplo: [`monitoring/zabbix/agent2/zabbix_agent2.conf.example`](../../monitoring/zabbix/agent2/zabbix_agent2.conf.example)  
Cadastro do host: [`monitoring/zabbix/scripts/register-host.md`](../../monitoring/zabbix/scripts/register-host.md)

## Portas

| Serviço | Bind | Observação |
|---------|------|------------|
| Zabbix Web | `127.0.0.1:8081` | Só localhost / túnel SSH |
| Zabbix Server `10051` | não publicado | Passive checks (Server → Agent `:10050`) |
| Agent 2 | host `:10050` | Firewall restringe origem à subnet `monitoring` |
| `zabbix-db` | não publicado | Volume `zabbix_pgdata` |

## Volumes

- `warehouseflow-monitoring_zabbix_pgdata` → dados do PostgreSQL do Zabbix

## Inicialização (stack Docker)

```bash
cp .env.monitoring.example .env.monitoring
# Editar senhas e APP_NETWORK / ZABBIX_AGENT_HOST

# Rede da app precisa existir
docker network ls
# Se necessário: docker network create warehouseflow_default

docker compose -p warehouseflow-monitoring \
  -f docker-compose.monitoring.yml \
  --env-file .env.monitoring up -d

docker compose -p warehouseflow-monitoring -f docker-compose.monitoring.yml ps
```

Acesso local:

```bash
# Na própria máquina
xdg-open http://127.0.0.1:8081

# Remoto via túnel SSH
ssh -L 8081:127.0.0.1:8081 user@debian-host
```

Login inicial: `Admin` / `zabbix` — **trocar a senha imediatamente**.

## Agent 2 no Debian 12

```bash
wget https://repo.zabbix.com/zabbix/7.0/debian/pool/main/z/zabbix-release/zabbix-release_latest_7.0+debian12_all.deb
sudo dpkg -i zabbix-release_latest_7.0+debian12_all.deb
sudo apt-get update
sudo apt-get install -y zabbix-agent2
```

Ajuste `/etc/zabbix/zabbix_agent2.conf` com base no exemplo do repositório:

- `Hostname=Debian-WarehouseFlow`
- `Server=<MONITORING_SUBNET ou IP do zabbix-server>`
- `ListenPort=10050`

```bash
sudo systemctl enable --now zabbix-agent2
zabbix_agent2 -t agent.hostname
```

## Server → Agent (IP real, sem host.docker.internal)

No mesmo host, o Server em Docker alcança o Agent pelo IP do host visto da bridge, tipicamente o gateway `docker0`:

```bash
ip -4 addr show docker0 | awk '/inet /{print $2}' | cut -d/ -f1
# Ex.: 172.17.0.1 → use como interface Agent na UI e em ZABBIX_AGENT_HOST
```

Na UI: Host `Debian-WarehouseFlow`, interface Agent = esse IP, porta `10050`, template `Linux by Zabbix agent`.

## Firewall (ufw)

```bash
SUBNET=$(docker network inspect warehouseflow-monitoring_monitoring \
  -f '{{(index .IPAM.Config 0).Subnet}}')
sudo ufw allow from "$SUBNET" to any port 10050 proto tcp comment 'zabbix-agent2'
sudo ufw reload
```

Não expor `10050`, `8081`, `10051` na internet / Security Group da EC2.

## Alertas

Triggers do template Linux (CPU, RAM, disco, agent unavailable). Ajuste thresholds em **Configuration → Templates** se necessário.

## Recuperação

```bash
# Parar / subir de novo (dados no volume)
docker compose -p warehouseflow-monitoring -f docker-compose.monitoring.yml down
docker compose -p warehouseflow-monitoring -f docker-compose.monitoring.yml --env-file .env.monitoring up -d

# Backup do DB Zabbix
docker compose -p warehouseflow-monitoring -f docker-compose.monitoring.yml exec -T zabbix-db \
  pg_dump -U zabbix zabbix > zabbix-backup-$(date +%F).sql
```

## Pressão de memória

Ordem sugerida para desligar temporariamente: Grafana/Prometheus/exporters → `zabbix-web` → `zabbix-server`+`zabbix-db`. Nunca derrubar o Compose da aplicação por causa do monitoramento.
