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

## SMTP e alertas por e-mail

Os alertas são provisionados no Git, em `monitoring/grafana/provisioning/alerting/`:

| Arquivo | Conteúdo |
|---------|----------|
| `contact-points.yml` | Contact Point `warehouseflow-email` (e-mail para `ALERT_EMAIL_TO`) |
| `notification-policies.yml` | Política raiz que envia tudo para `warehouseflow-email` |
| `alert-rules.yml` | Grupo `warehouseflow-infra`, pasta `WarehouseFlow`, cinco regras |

Regras (equivalentes às de `monitoring/prometheus/alerts.yml`, que não têm Alertmanager e não enviam e-mail):

| uid | Condição | for | Severidade |
|-----|----------|-----|------------|
| `wf-target-down` | `up == bool 0` | 5m | warning |
| `wf-health-failing` | `probe_success{probe="health",app="warehouseflow"} == bool 0` | 2m | critical |
| `wf-ready-failing` | `probe_success{probe="ready",app="warehouseflow"} == bool 0` | 2m | critical |
| `wf-host-high-memory` | memória do host > 90% | 5m | warning |
| `wf-host-disk-low` | disco com menos de 10% livre | 10m | warning |

O modificador `bool` faz a comparação devolver `1` quando o problema existe, por isso o threshold é sempre `gt 0`. Para ajustar limites ou janelas, edite `alert-rules.yml` e recrie o Grafana.

### 1. Variáveis (`.env.monitoring` no servidor)

Preencha no `.env.monitoring` existente. Acrescente as linhas, não substitua o arquivo. Nunca commite esse arquivo.

```
GF_SMTP_ENABLED=true
SMTP_HOST=smtp.gmail.com:587
SMTP_USER=<usuário SMTP, normalmente o e-mail completo>
SMTP_PASSWORD=<SENHA_DE_APP>
SMTP_FROM_ADDRESS=<remetente, normalmente igual ao usuário>
SMTP_FROM_NAME=WarehouseFlow Monitoramento
GF_SMTP_STARTTLS_POLICY=MandatoryStartTLS
ALERT_EMAIL_TO=<destinatário dos alertas>
```

- `SMTP_HOST` inclui a porta (`host:587`).
- `ALERT_EMAIL_TO` é obrigatório. Vários destinatários separados por `;`. Sem ele, o Compose recusa subir o Grafana, porque o Contact Point de e-mail não aceita endereço vazio.
- Valores com `#`, `$` ou espaços devem ficar entre aspas simples.
- Com `GF_SMTP_ENABLED=false` (padrão), o Grafana sobe normalmente e o e-mail não é enviado.

### 2. Provedores

- **Gmail:** `smtp.gmail.com:587`, usuário = e-mail completo, senha de app (exige verificação em duas etapas), `MandatoryStartTLS`. Crie a senha em https://myaccount.google.com/apppasswords.
- **Microsoft 365 / Outlook:** `smtp.office365.com:587`, com SMTP AUTH habilitado na caixa. Se o tenant bloquear autenticação básica, use SMTP corporativo ou relay.
- **SMTP corporativo:** host e porta fornecidos pelo administrador, `MandatoryStartTLS` em 587. Use `NoStartTLS` só em relay interno confiável.

### 3. Aplicar a mudança no servidor

Atualiza só o Grafana. Não recria a stack nem os volumes:

```bash
cd /opt/warehouseflow/staging
git pull
docker compose -p warehouseflow-monitoring -f docker-compose.monitoring.yml --env-file .env.monitoring up -d --no-deps grafana
```

`restart` não relê o ambiente. `up -d --no-deps grafana` recria apenas o container do Grafana e preserva `grafana_data`.

### 4. Testar

Em Alerting → Contact points → `warehouseflow-email` → **Test**. O e-mail deve chegar ao destinatário (verifique também o spam).

### 5. Logs e verificação (sem expor senha)

```bash
docker logs --tail 50 warehouseflow-monitoring-grafana-1 2>&1 | grep -iE 'smtp|email|notif|provision'
docker exec warehouseflow-monitoring-grafana-1 printenv | grep -E '^(GF_SMTP_(ENABLED|HOST|USER|FROM_ADDRESS|FROM_NAME|STARTTLS_POLICY)|ALERT_EMAIL_TO)='
```

O segundo comando não mostra `SMTP_PASSWORD`. Se o nome do container for outro, use `docker ps`.

Falhas comuns:

| Sintoma | Causa provável |
|---------|----------------|
| `ALERT_EMAIL_TO required` | Variável ausente no `.env.monitoring` |
| `535 Username and Password not accepted` | Senha normal em vez de senha de app, ou espaços na senha |
| `SMTP not configured` nos logs | `GF_SMTP_ENABLED` não está `true` ou `SMTP_HOST` vazio |
| Porta 587 não conecta | Saída bloqueada pela rede ou pelo provedor |
| E-mail não chega, sem erro | Verifique spam e o `SMTP_FROM_ADDRESS` |

Nunca cole senha SMTP no chat, em logs ou na documentação.

## Segurança

- Não publicar `3000` em `0.0.0.0` nem no Security Group da EC2.
- Não habilitar anonymous auth.
- Em pressão de memória, Grafana é um dos primeiros serviços a desligar (após ou junto com Prometheus/exporters). Ver [prometheus.md](prometheus.md) e [zabbix.md](zabbix.md).
