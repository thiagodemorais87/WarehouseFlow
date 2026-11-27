# WarehouseFlow — CI/CD (GitHub Actions)

Pipeline de integração e entrega contínua: CI nos runners do GitHub, imagens no GitHub Container Registry (GHCR) e deploy por um runner self-hosted na VM Debian. Staging é automático; produção exige aprovação.

## Visão geral

```mermaid
flowchart LR
  pr[PullRequest] --> ci
  pushDev[push dev] --> ci
  pushStg[push staging] --> ci
  pushMaster[push master] --> ci
  subgraph ci [CI em ubuntu-latest]
    quality[Qualidade]
    tests["Testes SQLite e PostgreSQL"]
    front[Frontend]
    dockerCfg[Docker config]
    build["Build e smoke test"]
  end
  ci --> publish["Publicar GHCR (staging e master)"]
  publish --> depStg["Deploy staging (self-hosted)"]
  publish --> approval[Aprovacao manual]
  approval --> depProd["Deploy production (self-hosted)"]
```

| Evento | O que roda |
|--------|-----------|
| Pull request para `dev`, `staging` ou `master` | Só CI |
| Push em `dev` | Só CI |
| Push em `staging` (merge do PR `dev` → `staging`) | CI → publish → deploy staging |
| Push em `master` (merge do PR `staging` → `master`) | CI → publish → **aprovação** → deploy production |

Publicação e deploy dependem (`needs`) de todos os jobs de CI na mesma execução: sem CI verde, nada é publicado nem implantado.

Arquivos:

| Arquivo | Função |
|---------|--------|
| [`.github/workflows/ci-cd.yml`](../../.github/workflows/ci-cd.yml) | CI, publish e deploy |
| [`.github/workflows/rollback.yml`](../../.github/workflows/rollback.yml) | Rollback manual |
| [`deploy/scripts/deploy.sh`](../../deploy/scripts/deploy.sh) | Deploy no servidor (com rollback automático) |
| [`deploy/scripts/rollback.sh`](../../deploy/scripts/rollback.sh) | Rollback no servidor |
| [`deploy/scripts/healthcheck.sh`](../../deploy/scripts/healthcheck.sh) | Validação `/health` + `/ready` |
| [`deploy/scripts/ghcr.sh`](../../deploy/scripts/ghcr.sh) | Login, push, pull e consulta no GHCR com novas tentativas em falha de rede |
| [`deploy/scripts/common.sh`](../../deploy/scripts/common.sh) | Funções compartilhadas |
| [`scripts/ci/check_frontend.py`](../../scripts/ci/check_frontend.py) | Validação do frontend |
| [`ruff.toml`](../../ruff.toml) | Regras do ruff (só erros reais) |

## Jobs de CI

| Job | Verifica |
|-----|----------|
| Qualidade | `ruff check` (sintaxe, nomes indefinidos), `compileall` do backend, `actionlint` dos workflows, `shellcheck` dos scripts, `hadolint` dos Dockerfiles (falha só em erro) |
| Testes (sqlite) | Suíte completa `pytest` em SQLite em memória (como no desenvolvimento) |
| Testes (postgres) | Mesma suíte com `TEST_DATABASE_URL` num PostgreSQL 16 descartável: ativa os testes de schema, seed, constraints e CRUD no PostgreSQL |
| Frontend | Parse de todos os templates Jinja2, existência de templates referenciados e de arquivos `/static/...`, `node --check` em cada JS |
| Configuração Docker | `docker compose config` dos três Compose (dev, prod com os exemplos de staging e produção, monitoramento) e `nginx -t` das duas confs |
| Build e smoke test | Build das imagens API e Nginx, sobe `docker-compose.prod.yml` num projeto descartável e valida `/health` (versão = tag) e `/ready` via Nginx |

Resultados: resumo em cada execução (aba **Summary**) e artefatos `pytest-sqlite`, `pytest-postgres` (JUnit + log) e `smoke-logs` (em falha).

## Imagens

- `ghcr.io/<owner>/warehouseflow-api` e `ghcr.io/<owner>/warehouseflow-nginx`
- Tags: `sha-<7 primeiros do commit>` (imutável, usada no deploy) e o nome do branch (`staging` ou `master`)
- A imagem publicada é a mesma que passou no smoke test (exportada do job de build, sem rebuild)
- Se a tag `sha-...` já existe no GHCR (re-execução do mesmo commit), nada é reenviado: a tag do branch é apontada para a imagem existente no próprio registry
- Autenticação com o `GITHUB_TOKEN` automático: nenhuma credencial de registry em Secrets
- Login, push, pull e consulta usam `deploy/scripts/ghcr.sh`, que classifica a saída do Docker:
  - **rede** (timeout, `502`/`503`/`504`, conexão): repetido até 5 vezes (espera de 5, 10, 20 e 40 s);
  - **credencial ou permissão** (`401`/`403`, `unauthorized`, `denied`): falha na primeira tentativa, com mensagem própria;
  - **não existe** (`404`, `manifest unknown`): falha na hora ao baixar ou enviar; na consulta de tag significa "ainda não publicada";
  - **Docker local** (sem acesso ao socket do runner): falha na hora, sem culpar o registry.
- Na consulta de tag existente, só "manifest inexistente" conta como ausente. Erro de autenticação, de rede (após 5 tentativas) ou desconhecido interrompe o job de publicação: erro nunca é tratado como imagem ausente.

`docker-compose.prod.yml` usa `${API_IMAGE:-warehouseflow-api}:${IMAGE_TAG:-${APP_VERSION:-latest}}`. Sem essas variáveis, o deploy manual com `up -d --build` continua igual.

## O que o deploy faz no servidor

`deploy/scripts/deploy.sh <ambiente> <tag>`, executado pelo runner no diretório `DEPLOY_PATH`:

1. **Pré-checagem**: argumentos, diretório, clone Git, `docker`, `curl` e Secrets. Sem o diretório, falha com "Ambiente production ainda não criado". Cada Secret é conferido sem exibir o valor (só nome e tamanho): quebra de linha no fim é removida com aviso; quebra no meio, valor entre aspas, vazio ou `SECRET_KEY` com menos de 32 caracteres interrompem.
2. **Autenticação no banco**: com o `db` em execução, um container temporário (mesma imagem do db) conecta por TCP no serviço `db` com `POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_DB` numa sessão só leitura (`select 1`). A senha vai pelo stdin, nunca por argumento. Qualquer resultado diferente de sucesso (senha recusada, usuário/banco inexistente, rede, timeout) interrompe. Banco parado com volume existente também interrompe; sem banco e sem volume é o primeiro deploy.
3. **Download das imagens** (`docker pull` com novas tentativas).
4. **Git**: `git fetch` + `git merge --ff-only <sha>` no branch do ambiente (sem `reset`/`force`; falha se houver divergência).
5. **Backup do banco** (`pg_dump -Fc` em `backups/<ambiente>-predeploy-*.dump`): obrigatório em produção; em staging só com a Variable `BACKUP_DB=true`.
6. **Ponto de rollback**: marca as imagens em execução como `warehouseflow-api:rollback-<ambiente>` e `warehouseflow-nginx:rollback-<ambiente>`.
7. **`.env.<ambiente>`**: gerado a partir dos Secrets/Variables (permissão 600, nunca exibido). Valores entre aspas duplas com `\`, `"` e `$` escapados: senhas com aspas, cifrão, barra invertida, espaço, `@`, `%` ou `#` chegam intactas ao container. O anterior vai para `.deploy/backups/` (mantém os 20 últimos).
8. **Atualização**: `up -d --no-build --no-deps --wait api frontend`. O `db` só é criado se não estiver rodando; nunca há `down` nem remoção de volume.
9. **Health check**: `http://127.0.0.1:<HTTP_PORT>/health` com `version` igual à tag e `/ready` 200.
10. **Falha em 8 ou 9**: restaura o `.env` anterior, volta para as imagens `:rollback-<ambiente>`, valida a saúde e marca o job como falho.
11. **Registro**: linha em `.deploy/history.log` (data, ambiente, tag, commit, resultado), log da execução em `.deploy/logs/` e resumo no GitHub.

Se as etapas 1 e 2 falharem, nada é alterado no servidor e a mensagem termina com "nada foi alterado no servidor". Se a etapa 3 (download) falhar, serviços, banco, Git e `.env` continuam intactos, mas o Docker pode ter baixado imagens para o **cache local**: a mensagem diz "não foram alterados; o Docker pode ter baixado imagens para o cache local". A partir do Git (etapa 4) a mensagem avisa que o servidor já havia sido alterado, e vale o rollback automático. O deploy **nunca** altera a senha do banco.

Migrations SQL **não** são executadas pelo pipeline (como em [deploy.md](deploy.md#migrations-sql-bancos-já-existentes)).

## Configuração (uma vez)

### 1. Runner self-hosted na VM

No GitHub: **Settings → Actions → Runners → New self-hosted runner → Linux**. A página mostra os comandos de download e um token temporário. Na VM, como `vboxuser`:

```bash
mkdir -p ~/actions-runner && cd ~/actions-runner
# Baixe e extraia o pacote com os comandos exibidos na página do GitHub (curl + tar).
./config.sh --url https://github.com/thiagodemorais87/WarehouseFlow \
  --token <TOKEN_DA_PAGINA> --name warehouseflow-debian --unattended
sudo ./svc.sh install vboxuser
sudo ./svc.sh start
sudo ./svc.sh status
```

O runner deve ficar só com as labels padrão (`self-hosted`, `Linux`, `X64`). Os workflows usam `runs-on: self-hosted`, então não é preciso criar label customizada. Se o runner já tiver sido registrado com `--labels warehouseflow`, basta removê-la em Settings → Actions → Runners (não é necessário reinstalar).

Requisitos do usuário do runner:

- Estar no grupo `docker` (`groups vboxuser`; se faltar: `sudo usermod -aG docker vboxuser` e reinicie o serviço do runner).
- Ser dono do clone em `/opt/warehouseflow/staging` (evita o erro "dubious ownership" do Git).
- `git` e `curl` instalados.

O token do `config.sh` é de uso único e expira em 1 hora; não o salve em arquivos nem envie em mensagens.

### 2. Environments e Secrets

**Settings → Environments → New environment**.

Environment **`staging`**:

- Deployment branches: **Selected branches** → `staging`
- Secrets (**Add environment secret**):

| Secret | Valor |
|--------|-------|
| `POSTGRES_USER` | Usuário do PostgreSQL de staging |
| `POSTGRES_PASSWORD` | Senha **atual** do PostgreSQL de staging |
| `POSTGRES_DB` | Nome do banco de staging |
| `SECRET_KEY` | Chave JWT de staging: aleatória, **mínimo 32 caracteres** (a API recusa iniciar em staging/produção com chave fraca). Gere com `openssl rand -hex 32` |

- Variables (**Add environment variable**):

| Variable | Exemplo |
|----------|---------|
| `DEPLOY_PATH` | `/opt/warehouseflow/staging` |
| `HTTP_PORT` | `80` |
| `APP_ENV` | `staging` |
| `COOKIE_SECURE` | `false` (até ter HTTPS) |
| `ENABLE_DOCS` | `false` |
| `BACKUP_DB` | `true` ou `false` (opcional) |

Environment **`production`**: os mesmos Secrets e Variables com os valores de produção, mais:

- **Required reviewers**: você (e quem mais aprovar deploys)
- Deployment branches: **Selected branches** → `master`
- `DEPLOY_PATH=/opt/warehouseflow/production`; se ficar na mesma VM do staging, use outra `HTTP_PORT` (ex.: `8088`)

> A senha do banco no Secret precisa ser **idêntica** à atual. O volume do PostgreSQL já foi inicializado: trocar `POSTGRES_PASSWORD` no Secret não muda a senha do banco. O deploy confirma a senha com uma conexão real antes de alterar qualquer coisa e para se ela não autenticar.

Cuidados ao salvar os Secrets:

- **Secret de environment tem prioridade** sobre um Secret de mesmo nome no repositório. Edite o do environment (**Settings → Environments → staging**); se existir um antigo em *Repository secrets*, apague-o para evitar confusão.
- Cole **só o valor**: sem aspas em volta e sem Enter no fim (copiar a linha inteira no PuTTY costuma trazer a quebra de linha).
- Se a senha estiver só na `DATABASE_URL`, ela pode estar codificada para URL (`%40` = `@`, `%23` = `#`, `%25` = `%`...). O Secret deve ter a senha **decodificada**.

Para copiar os valores atuais do staging para os Secrets, consulte o arquivo **na VM** e digite os valores direto no GitHub (nunca em chat, issue ou commit):

```bash
cd /opt/warehouseflow/staging
grep -E '^(POSTGRES_USER|POSTGRES_DB|HTTP_PORT|APP_ENV|COOKIE_SECURE|ENABLE_DOCS)=' .env.staging
nano .env.staging   # copie POSTGRES_PASSWORD e SECRET_KEY daqui; saia sem salvar
```

Para conferir o tamanho da senha do arquivo sem exibi-la (compare com o "N caracteres" do resumo do deploy):

```bash
grep '^POSTGRES_PASSWORD=' .env.staging | cut -d= -f2- | awk '{print "tamanho com eventuais aspas:", length($0)}'
```

### 3. Proteção de branches

**Settings → Branches → Add branch ruleset** (ou *branch protection rule*) para `staging` e `master`:

- Require a pull request before merging
- Require status checks to pass: `Qualidade`, `Testes (sqlite)`, `Testes (postgres)`, `Frontend`, `Configuração Docker`, `Build e smoke test`
- Block force pushes

Os nomes dos checks aparecem para seleção depois da primeira execução do workflow.

### 4. Branch padrão

O botão **Run workflow** do `rollback.yml` só aparece se o workflow estiver no branch padrão (hoje `main`). Escolha uma opção:

- **Settings → General → Default branch** → `master` (recomendado, fim do fluxo `dev → staging → master`), ou
- levar `.github/workflows/` também para `main`.

### 5. Permissões do Actions

- **Settings → Actions → General → Fork pull request workflows**: exigir aprovação para colaboradores externos. Os jobs self-hosted nunca rodam em `pull_request`, mas isso reduz o risco.
- **Workflow permissions**: pode ficar *Read repository contents*; o workflow pede `packages: write` só no job de publish.

### 6. Pacotes no GHCR

Após o primeiro publish, os pacotes `warehouseflow-api` e `warehouseflow-nginx` aparecem em **Packages** do perfil. Confira em **Package settings → Manage Actions access** que o repositório `WarehouseFlow` tem acesso (normalmente automático, pela label `org.opencontainers.image.source`).

## Primeiro deploy em staging

1. Runner online (**Settings → Actions → Runners** → `warehouseflow-debian` *Idle*).
2. Environment `staging` com Secrets e Variables preenchidos.
3. Na VM, o clone em `/opt/warehouseflow/staging` está no branch `staging` e sem alterações em arquivos versionados (`git status`).
4. Abra e faça merge do PR `dev` → `staging`.
5. Acompanhe em **Actions → CI/CD**. Ao final, na VM:

```bash
cd /opt/warehouseflow/staging
cat .deploy/history.log
curl -s http://127.0.0.1/health
docker compose -p warehouseflow-staging --env-file .env.staging -f docker-compose.prod.yml ps
```

O primeiro deploy substitui o `.env.staging` pelo gerado; o original fica em `.deploy/backups/`.

## Produção

Enquanto `/opt/warehouseflow/production` não existir, todo push em `master` cria um deploy aguardando aprovação que falha na pré-checagem com a mensagem "Ambiente production ainda não criado". Rejeite a aprovação ou deixe falhar.

Para criar o ambiente (na mesma VM ou em outro servidor com runner próprio):

```bash
sudo mkdir -p /opt/warehouseflow/production
sudo chown vboxuser:vboxuser /opt/warehouseflow/production
git clone -b master https://github.com/thiagodemorais87/WarehouseFlow /opt/warehouseflow/production
```

Depois preencha o environment `production` e faça um novo merge em `master` (ou reexecute o job).

## Rollback

**Automático**: se `up` ou o health check falharem, o `deploy.sh` volta sozinho para a versão anterior. Falhas antes disso (Secrets, autenticação no banco, download das imagens) interrompem sem alterar nada.

**Manual (GitHub)**: **Actions → Rollback → Run workflow**:

- *Use workflow from*: `staging` para staging, `master` para production (regra de branches do environment)
- `environment`: `staging` ou `production` (production pede aprovação)
- `image_tag` vazio: volta para a versão anterior ao último deploy (imagens locais `:rollback-<ambiente>`)
- `image_tag` preenchido (ex.: `sha-abc1234`): implanta essa tag do GHCR. Veja as tags em `.deploy/history.log` ou em **Packages**

**Manual (na VM, sem GitHub)**: ver [rollback.md](rollback.md#rollback-pelo-cicd-imagens).

O rollback troca só as imagens; o clone Git do servidor continua no commit mais novo. Se a mudança problemática estiver em `docker-compose.prod.yml` ou nas confs, reverta o commit e faça um novo deploy.

## Logs e resultados

| Onde | O quê |
|------|-------|
| Actions → execução → **Summary** | Testes (aprovados/falhas/ignorados), imagens publicadas, resultado do deploy |
| Actions → execução → **Artifacts** | `pytest-*` (JUnit + log), `smoke-logs`, `deploy-<ambiente>-log`, `rollback-<ambiente>-log`. O envio do log é opcional (`continue-on-error`): se a rede da VM falhar no upload, o job continua refletindo o resultado do deploy |
| VM: `.deploy/logs/` | Log de cada execução, gravado uma única vez (`<ambiente>-<modo>-<data>-<pid>.log`, permissão 600, últimos 30), inclusive quando a pré-checagem falha. Falha ao gravar só gera um `AVISO` e nunca troca o resultado do deploy. Falhas antes de existir o diretório do ambiente (ex.: `DEPLOY_PATH` ausente) ficam só no log do runner, enviado como artefato |
| VM: `.deploy/history.log` | Histórico de deploys e rollbacks |
| VM: `backups/` | Dumps antes do deploy (produção sempre). Não há limpeza automática: mova para fora da VM periodicamente |

## Segurança

- Nenhuma senha no repositório: segredos só em GitHub Environments; o `.env` gerado tem permissão 600 e não é exibido nos logs (o GitHub mascara os Secrets).
- Jobs self-hosted só rodam em `push` para `staging`/`master` e em `workflow_dispatch`, nunca em `pull_request`.
- O usuário do runner no grupo `docker` equivale a root na VM: não instale outros serviços sob esse usuário se a VM for compartilhada.
- Os scripts nunca exibem segredos: mensagens mostram só nome e tamanho, e log e resumo passam por um filtro que troca qualquer ocorrência de `POSTGRES_PASSWORD`, `SECRET_KEY` ou do token do GHCR por `***`. Senha e token vão por stdin, nunca como argumento de processo.

## Alternativa futura: deploy por SSH (EC2)

Para um servidor com IP público, dá para trocar o runner self-hosted por SSH a partir dos runners do GitHub. Secrets necessários (só então):

| Secret | Conteúdo |
|--------|----------|
| `DEPLOY_SSH_KEY` | Chave privada de deploy (gerada só para isso, sem senha) |
| `DEPLOY_HOST` | IP ou DNS do servidor |
| `DEPLOY_USER` | Usuário de deploy no servidor |

Restrinja a porta 22 no Security Group e nunca envie a chave privada em mensagens ou commits.

## Validação local

Os mesmos checks do CI, em containers descartáveis (PowerShell, na raiz do repositório):

```powershell
$root = $PWD.Path
docker run --rm -v "${root}:/repo" -w /repo rhysd/actionlint:1.7.12 -no-color
docker run --rm -v "${root}:/mnt" -w /mnt koalaman/shellcheck:stable -x deploy/scripts/common.sh deploy/scripts/deploy.sh deploy/scripts/rollback.sh deploy/scripts/healthcheck.sh deploy/scripts/ghcr.sh
docker run --rm -e PYTHONPYCACHEPREFIX=/tmp/pycache -v "${root}:/src" -w /src python:3.12-slim sh -c "pip install -q -r requirements.txt ruff==0.8.4 && ruff check --no-cache . && python scripts/ci/check_frontend.py && python -m pytest -q -p no:cacheprovider"
docker compose -p warehouseflow-staging --env-file .env.staging.example -f docker-compose.prod.yml config -q
```

## Problemas comuns

| Sintoma | Causa provável |
|---------|----------------|
| Job de deploy fica em *Queued* | Runner offline |
| `variáveis obrigatórias ausentes` | Secrets/Variables não criados no environment |
| `... foi salvo com aspas em volta` | Secret salvo como `'senha'` ou `"senha"`: salve só o valor |
| `AVISO: ... quebra de linha no fim removida` | Secret colado com Enter no fim; o deploy segue, mas vale salvar de novo sem a quebra |
| `não foi possível confirmar POSTGRES_PASSWORD: o PostgreSQL recusou a senha` | Secret diferente da senha atual (confira o Secret do **environment**, que tem prioridade, e se a senha não foi copiada codificada da `DATABASE_URL`) |
| `não foi possível confirmar POSTGRES_PASSWORD: falha de rede` / `tempo esgotado` | Container db sem rede ou travado; nada foi alterado. Verifique `docker ps` e rode de novo |
| `banco parado com dados existentes` | Container db parado: suba só o banco (`docker compose ... up -d db`) e rode o deploy de novo |
| `login em ghcr.io: tentativa N/5 falhou (timeout/erro de rede)` | Instabilidade de rede; repetido automaticamente. Se esgotar, rode o job de novo |
| `o GHCR recusou a credencial ou a permissão` | Permissão do job (`packages`) ou acesso do repositório ao pacote (item 6 da configuração) |
| `a imagem/tag não existe no registry` | A tag não foi publicada (confira o job "Publicar no GHCR" do mesmo commit) |
| `NÃO tratado como imagem ausente` (job de publicação) | A consulta da tag falhou por rede, permissão ou erro desconhecido; rode o job de novo ou corrija a permissão |
| `o Docker do runner não está acessível` | Usuário do runner sem acesso ao `docker.sock` ou Docker parado na VM |
| `Ambiente ... ainda não criado` | `DEPLOY_PATH` não existe no servidor |
| `não foi possível avançar ... fast-forward` | Commits ou alterações locais no clone do servidor |
| `denied` no `docker pull` | Repositório sem acesso ao pacote no GHCR (item 6 da configuração) |
| `/ready` falha e há rollback | API sem acesso ao banco após a troca (ver logs no artefato ou em `.deploy/logs/`) |
| API reinicia com `SECRET_KEY fraca ou placeholder` | `SECRET_KEY` com menos de 32 caracteres ou valor de exemplo |
| `permission denied ... docker.sock` | Usuário do runner fora do grupo `docker` |
