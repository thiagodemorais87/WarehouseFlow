# Cadastro do host Debian no Zabbix

Pré-requisitos: stack `docker-compose.monitoring.yml` saudável e Agent 2 rodando no host.

## 1. Descobrir IP do Agent visto pelo Server

No host Debian:

```bash
# Gateway docker0 (caso comum same-host)
ip -4 addr show docker0 | awk '/inet /{print $2}' | cut -d/ -f1

# Ou IP da interface principal alcançável pelos containers
ip -4 route get 1.1.1.1 | awk '{print $7; exit}'
```

Defina o mesmo valor em `.env.monitoring` como `ZABBIX_AGENT_HOST` (documentação; a UI usa o IP no cadastro do host).

## 2. Firewall (ufw)

```bash
# Subnet da rede monitoring
docker network inspect warehouseflow-monitoring_monitoring \
  -f '{{(index .IPAM.Config 0).Subnet}}'

sudo ufw allow from <MONITORING_SUBNET> to any port 10050 proto tcp comment 'zabbix-agent2'
sudo ufw reload
sudo ufw status numbered
```

Não abra 10050 para `Anywhere`.

## 3. UI Zabbix

1. Túnel: `ssh -L 8081:127.0.0.1:8081 user@debian-host`
2. Abrir `http://127.0.0.1:8081` — login inicial `Admin` / `zabbix` (trocar senha imediatamente).
3. **Data collection → Hosts → Create host**
   - Host name: `Debian-WarehouseFlow`
   - Templates: `Linux by Zabbix agent`
   - Interfaces: Agent → IP = `ZABBIX_AGENT_HOST` (ex. `172.17.0.1`), port `10050`
4. Aguardar Availability = green.
5. Verificar Latest data: CPU, memory, filesystem, agent.ping.

## 4. Alertas básicos (triggers do template)

O template `Linux by Zabbix agent` já inclui triggers de CPU alta, memória, disco e agent unavailable. Ajuste thresholds se necessário em **Configuration → Templates**.

## 5. Teste CLI no host

```bash
sudo systemctl status zabbix-agent2
zabbix_agent2 -t agent.hostname
zabbix_agent2 -t system.cpu.util
zabbix_agent2 -t vm.memory.size[available]
zabbix_agent2 -t vfs.fs.size[/,pfree]
```

Do container server (conectividade):

```bash
docker compose -p warehouseflow-monitoring -f docker-compose.monitoring.yml exec zabbix-server \
  sh -c 'nc -zv "$ZABBIX_AGENT_HOST" 10050' 
# Se a variável não existir no container, use o IP explícito:
docker compose -p warehouseflow-monitoring -f docker-compose.monitoring.yml exec zabbix-server \
  sh -c 'nc -zv 172.17.0.1 10050'
```
