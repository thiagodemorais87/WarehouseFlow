# WarehouseFlow — Debian 12 (VirtualBox / servidor)

Comandos para instalar Docker e preparar os diretórios de staging e produção.

## Pacotes base

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg git
```

## Docker Engine + Compose plugin

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian bookworm stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo usermod -aG docker "$USER"
# Faça logout/login para o grupo docker valer
docker version
docker compose version
```

## Diretórios de ambiente

```bash
sudo mkdir -p /opt/warehouseflow/staging /opt/warehouseflow/production
sudo chown -R "$USER":"$USER" /opt/warehouseflow
```

## Clonar / atualizar o código

```bash
# Staging (branch staging ou cópia a partir de dev, conforme o fluxo do time)
cd /opt/warehouseflow/staging
git clone <URL_DO_REPOSITORIO> .
git checkout staging   # ou a branch acordada para homologação

# Produção
cd /opt/warehouseflow/production
git clone <URL_DO_REPOSITORIO> .
git checkout master
```

Se o repositório já existir, use `git fetch` + `git checkout` + `git pull` em vez de clonar de novo.

## Arquivos de ambiente

```bash
cd /opt/warehouseflow/staging
cp .env.staging.example .env.staging
nano .env.staging   # SECRET_KEY, POSTGRES_PASSWORD, DATABASE_URL alinhados

cd /opt/warehouseflow/production
cp .env.production.example .env.production
nano .env.production
```

Gere uma `SECRET_KEY` forte (exemplo):

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Firewall (exemplo ufw)

```bash
sudo apt-get install -y ufw
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
# Após HTTPS:
# sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

Não abra a porta do PostgreSQL nem `8000` para a internet.

## Subir staging

```bash
cd /opt/warehouseflow/staging
docker compose -p warehouseflow-staging --env-file .env.staging -f docker-compose.prod.yml up -d --build
```

## Subir produção

```bash
cd /opt/warehouseflow/production
docker compose -p warehouseflow-production --env-file .env.production -f docker-compose.prod.yml up -d --build
```

## Validar

```bash
curl -s http://127.0.0.1/health
curl -s http://127.0.0.1/ready
# Ou pelo IP público da VM/EC2:
# curl -s http://IP_PUBLICO/health
```

## AWS EC2 (checklist)

1. AMI Debian 12 ou Ubuntu compatível; security group: SSH (seu IP), HTTP 80, depois HTTPS 443.
2. Repetir instalação Docker e diretórios acima.
3. Preferir IP elástico ou DNS; `server_name _` no Nginx aceita IP e domínio.
4. Após certificado TLS, definir `COOKIE_SECURE=true` e aplicar conf SSL (ver [deploy.md](deploy.md)).
