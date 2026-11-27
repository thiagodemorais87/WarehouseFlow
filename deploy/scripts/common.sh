#!/usr/bin/env bash
# Funções compartilhadas por deploy.sh, rollback.sh e healthcheck.sh.
# Uso: source "$(dirname "$0")/common.sh"

# Troca por *** qualquer ocorrência literal dos segredos conhecidos (defesa extra: as mensagens
# já não incluem valores). WF_PASSWORD_URLENC é a senha codificada para a DATABASE_URL.
redact() {
  local s="$1" v
  for v in "${POSTGRES_PASSWORD:-}" "${WF_PASSWORD_URLENC:-}" "${SECRET_KEY:-}" "${GHCR_TOKEN:-}"; do
    [ -n "$v" ] || continue
    s="${s//"$v"/"***"}"
  done
  printf '%s' "$s"
}

log() {
  local line
  line="$(redact "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*")"
  printf '%s\n' "$line" >&2
  if [ -n "${DEPLOY_LOG:-}" ]; then
    printf '%s\n' "$line" >> "$DEPLOY_LOG"
  fi
}

# Fase atual do deploy e o que já foi alterado (usado nas mensagens de erro):
#   WF_CHANGED=1  Git, .env, arquivo de backup, serviços ou banco
#   WF_CACHE=1    só o cache local de imagens do Docker (pull ou tag local)
WF_PHASE="${WF_PHASE:-}"
WF_CHANGED="${WF_CHANGED:-0}"
WF_CACHE="${WF_CACHE:-0}"

phase() {
  WF_PHASE="$1"
  log "== fase: $1 =="
}

die() {
  local msg="$*"
  if [ -n "${WF_PHASE:-}" ]; then
    msg="[fase: ${WF_PHASE}] ${msg}"
    if [ "${WF_CHANGED:-0}" = "1" ]; then
      msg="${msg} — o servidor já havia sido alterado nesta etapa (veja o log)"
    elif [ "${WF_CACHE:-0}" = "1" ]; then
      msg="${msg} — serviços, banco, Git e .env não foram alterados; o Docker pode ter baixado imagens para o cache local"
    else
      msg="${msg} — nada foi alterado no servidor (serviços, banco, Git e .env intactos)"
    fi
  fi
  log "ERRO: ${msg}"
  summary "**Falha:** ${msg}"
  exit 1
}

summary() {
  if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
    printf '%s\n' "$(redact "$*")" >> "$GITHUB_STEP_SUMMARY"
  fi
}

# Normaliza e valida uma variável sem nunca exibir o valor (só nome e tamanho).
# Remove CR/LF no fim (cópia de terminal); recusa quebra no meio e valor inteiro entre aspas.
# Uso: check_value NOME [secret]
check_value() {
  local name="$1" kind="${2:-var}" value trimmed notes=""
  value="${!name:-}"
  [ -n "$value" ] || die "${name} está vazio ou não foi definido (configure no environment '${WF_ENV:-?}' do GitHub)"

  trimmed="$value"
  while [[ "$trimmed" == *$'\n' || "$trimmed" == *$'\r' ]]; do
    trimmed="${trimmed%$'\n'}"
    trimmed="${trimmed%$'\r'}"
  done
  if [ "$trimmed" != "$value" ]; then
    [ -n "$trimmed" ] || die "${name} contém só quebras de linha"
    printf -v "$name" '%s' "$trimmed"
    export "${name?}"
    value="$trimmed"
    log "AVISO: ${name}: quebra de linha no fim removida (${#value} caracteres após a remoção)"
    notes="quebra de linha final removida"
  fi

  case "$value" in
    *$'\n'* | *$'\r'*) die "${name} contém quebra de linha no meio do valor (não suportado)" ;;
  esac
  if [ "${#value}" -ge 2 ] && [[ "$value" == \'*\' || "$value" == \"*\" ]]; then
    die "${name} foi salvo com aspas em volta: salve no GitHub só o valor, sem as aspas"
  fi

  if [ "$kind" = "secret" ]; then
    if [[ "$value" == *"://"* || "$value" == *"@db:"* || "$value" =~ %[0-9A-Fa-f]{2} ]]; then
      log "AVISO: ${name} parece copiado da DATABASE_URL ou codificado para URL; o Secret deve ter o valor decodificado"
      notes="${notes:+${notes}; }parece URL/codificado"
    fi
    if [[ "$value" == [[:space:]]* || "$value" == *[[:space:]] ]]; then
      log "AVISO: ${name} começa ou termina com espaço"
      notes="${notes:+${notes}; }espaço no início/fim"
    fi
    if [ "$name" = "SECRET_KEY" ] && [ "${#value}" -lt 32 ]; then
      die "SECRET_KEY tem ${#value} caracteres: o mínimo é 32 (a API não inicia em ${WF_ENV:-staging} com chave fraca)"
    fi
    log "${name}: ok (${#value} caracteres)"
    summary "- \`${name}\`: ok, ${#value} caracteres${notes:+ (${notes})}"
  fi
}

require_vars() {
  local missing=() name
  for name in "$@"; do
    [ -n "${!name:-}" ] || missing+=("$name")
  done
  if [ "${#missing[@]}" -gt 0 ]; then
    die "variáveis obrigatórias ausentes: ${missing[*]} (configure os Secrets/Variables do environment no GitHub)"
  fi
}

validate_env_name() {
  case "$1" in
    staging | production) ;;
    *) die "ambiente inválido: '$1' (use staging ou production)" ;;
  esac
}

validate_tag() {
  [[ "$1" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$ ]] || die "tag de imagem inválida: '$1'"
}

# Codifica um valor para uso em URL (senha na DATABASE_URL).
urlencode() {
  local LC_ALL=C s="$1" out="" c hex i
  for ((i = 0; i < ${#s}; i++)); do
    c="${s:i:1}"
    case "$c" in
      [a-zA-Z0-9.~_-]) out+="$c" ;;
      *)
        printf -v hex '%%%02X' "'$c"
        out+="$hex"
        ;;
    esac
  done
  printf '%s' "$out"
}

# Inicializa variáveis do ambiente alvo. Requer WF_ENV e DEPLOY_PATH.
init_target() {
  validate_env_name "$WF_ENV"
  if [ -z "${DEPLOY_PATH:-}" ]; then
    die "Ambiente ${WF_ENV} sem DEPLOY_PATH: crie a Variable DEPLOY_PATH no environment '${WF_ENV}' (veja docs/devops/ci-cd.md)"
  fi
  if [ ! -d "$DEPLOY_PATH" ]; then
    die "Ambiente ${WF_ENV} ainda não criado: o diretório ${DEPLOY_PATH} não existe no servidor (veja docs/devops/ci-cd.md)"
  fi
  [ -d "$DEPLOY_PATH/.git" ] || die "${DEPLOY_PATH} não é um clone Git do repositório"
  [ -f "$DEPLOY_PATH/docker-compose.prod.yml" ] || die "${DEPLOY_PATH}/docker-compose.prod.yml não encontrado"
  command -v docker >/dev/null 2>&1 || die "docker não encontrado no runner"
  command -v curl >/dev/null 2>&1 || die "curl não encontrado no runner"

  COMPOSE_PROJECT="warehouseflow-${WF_ENV}"
  ENV_FILE="${DEPLOY_PATH}/.env.${WF_ENV}"
  STATE_DIR="${DEPLOY_PATH}/.deploy"
  ROLLBACK_TAG="rollback-${WF_ENV}"
  mkdir -p "$STATE_DIR/backups"
  chmod 700 "$STATE_DIR"
}

# docker compose apontando para o ambiente alvo. Só o env file define a interpolação:
# as variáveis de segredo/imagem do processo são removidas para não sobrescrevê-lo.
compose() {
  env -u POSTGRES_USER -u POSTGRES_PASSWORD -u POSTGRES_DB -u SECRET_KEY -u DATABASE_URL \
    -u API_IMAGE -u NGINX_IMAGE -u IMAGE_TAG -u APP_VERSION -u APP_ENV \
    -u HTTP_PORT -u COOKIE_SECURE -u ENABLE_DOCS \
    docker compose -p "$COMPOSE_PROJECT" --env-file "$ENV_FILE" \
    -f "${DEPLOY_PATH}/docker-compose.prod.yml" "$@"
}

# Valor para env file do Compose: sempre entre aspas duplas, escapando \ " e $.
# Aspas simples não servem: o Compose não aceita valor entre aspas simples terminado em "\".
env_quote() {
  local v="$1" bs="\\" dq='"' dl='$'
  v="${v//"$bs"/"$bs$bs"}"
  v="${v//"$dq"/"$bs$dq"}"
  v="${v//"$dl"/"$bs$dl"}"
  printf '"%s"' "$v"
}

# Inverso de env_quote; também aceita 'valor' (env files antigos) e valor sem aspas.
env_unquote() {
  local v="$1" out="" i c
  case "$v" in
    \"*\")
      v="${v:1:${#v}-2}"
      for ((i = 0; i < ${#v}; i++)); do
        c="${v:i:1}"
        if [ "$c" = "\\" ] && [ $((i + 1)) -lt "${#v}" ]; then
          i=$((i + 1))
          c="${v:i:1}"
        fi
        out+="$c"
      done
      printf '%s' "$out"
      ;;
    \'*\') printf '%s' "${v:1:${#v}-2}" ;;
    *) printf '%s' "$v" ;;
  esac
}

# Lê KEY=valor de um env file.
env_get() {
  local key="$1" file="$2" line
  [ -f "$file" ] || return 0
  line="$(grep -E "^${key}=" "$file" | tail -n 1 || true)"
  env_unquote "${line#*=}"
}

# Define KEY="valor" num env file, preservando as demais linhas e a permissão 600.
env_set() {
  local key="$1" value="$2" file="$3" tmp
  tmp="$(mktemp "${STATE_DIR}/env.XXXXXX")"
  chmod 600 "$tmp"
  grep -vE "^${key}=" "$file" > "$tmp" || true
  printf '%s=%s\n' "$key" "$(env_quote "$value")" >> "$tmp"
  mv "$tmp" "$file"
}

# Confirma POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB com uma conexão PostgreSQL real e só leitura.
# Padrões (grep -E, sem diferenciar maiúsculas) da saída do psql/docker na checagem do banco.
WF_DB_AUTH_RE='password authentication failed'
WF_DB_ROLE_RE='role ".*" does not exist'
WF_DB_DATABASE_RE='database ".*" does not exist'
WF_DB_NETWORK_RE='could not translate host|connection refused|timeout expired|could not connect|no route to host|network is unreachable|network .* not found'

# Motivo (texto para o usuário) de uma falha na checagem do banco: db_error_reason <rc> <saída>.
db_error_reason() {
  local rc="$1" out="$2"
  if [ "$rc" -eq 124 ]; then
    printf 'tempo esgotado (60 s) ao conectar no banco'
  elif grep -Eqi "$WF_DB_AUTH_RE" <<<"$out"; then
    printf 'o PostgreSQL recusou a senha: o Secret POSTGRES_PASSWORD não é a senha atual do usuário %s' "${POSTGRES_USER:-?}"
  elif grep -Eqi "$WF_DB_ROLE_RE" <<<"$out"; then
    printf 'o usuário do Secret POSTGRES_USER (%s) não existe no banco' "${POSTGRES_USER:-?}"
  elif grep -Eqi "$WF_DB_DATABASE_RE" <<<"$out"; then
    printf 'o banco do Secret POSTGRES_DB (%s) não existe' "${POSTGRES_DB:-?}"
  elif grep -Eqi "$WF_DB_NETWORK_RE" <<<"$out"; then
    printf 'falha de rede ao conectar no serviço db'
  else
    printf 'erro inesperado na conexão (código %s)' "$rc"
  fi
}

# Conecta por TCP no serviço "db" a partir de um container temporário na rede do projeto, onde o
# pg_hba exige senha (o "trust" do official image vale só para socket/127.0.0.1). A senha vai pelo
# stdin: não aparece em argumentos de processo nem na configuração do container.
# Qualquer resultado diferente de sucesso interrompe o deploy.
check_db_auth() {
  local cid image net out rc=0 reason
  cid="$(service_container db)"
  if [ -z "$cid" ]; then
    if docker volume inspect "${COMPOSE_PROJECT}_pgdata" >/dev/null 2>&1; then
      die "banco parado com dados existentes (volume ${COMPOSE_PROJECT}_pgdata): inicie o serviço db e rode o deploy de novo — sem o banco em execução não dá para confirmar POSTGRES_PASSWORD"
    fi
    log "primeiro deploy: sem container db nem volume ${COMPOSE_PROJECT}_pgdata — o banco será criado com os Secrets"
    summary "- Banco: primeiro deploy (será criado com os Secrets)"
    return 0
  fi

  image="$(docker inspect -f '{{.Config.Image}}' "$cid")"
  net="${COMPOSE_PROJECT}_default"
  if ! docker inspect -f '{{range $k, $v := .NetworkSettings.Networks}}{{println $k}}{{end}}' "$cid" | grep -qx "$net"; then
    die "o container db não está na rede ${net}: não foi possível confirmar POSTGRES_PASSWORD"
  fi

  log "confirmando POSTGRES_PASSWORD com conexão real ao banco (usuário ${POSTGRES_USER}, banco ${POSTGRES_DB}, sessão só leitura)"
  # shellcheck disable=SC2016
  out="$(printf '%s\n' "$POSTGRES_PASSWORD" |
    PGUSER="$POSTGRES_USER" PGDATABASE="$POSTGRES_DB" timeout 60 \
      docker run --rm -i --pull never --network "$net" \
      -e PGUSER -e PGDATABASE -e PGCONNECT_TIMEOUT=10 \
      -e PGOPTIONS='-c default_transaction_read_only=on' \
      --entrypoint sh "$image" \
      -c 'IFS= read -r PGPASSWORD; export PGPASSWORD; exec psql -h db -X -q -v ON_ERROR_STOP=1 -tAc "select 1"' \
      2>&1)" || rc=$?

  if [ "$rc" -eq 0 ] && [ "$(printf '%s' "$out" | tr -d '[:space:]')" = "1" ]; then
    log "POSTGRES_PASSWORD confirmado: autentica no banco atual"
    summary "- Banco: autenticação confirmada (conexão só leitura)"
    return 0
  fi

  reason="$(db_error_reason "$rc" "$out")"
  log "saída da checagem: $(printf '%s\n' "$out" | sed '/^[[:space:]]*$/d' | tail -n 3 | tr '\n' ' ')"
  die "não foi possível confirmar POSTGRES_PASSWORD: ${reason}. O deploy não altera a senha do banco; corrija o Secret no environment '${WF_ENV}'"
}

# Cabeçalho do log (escrito antes de qualquer validação; uma única vez por execução, mesmo
# quando rollback.sh chama deploy.sh).
log_header() {
  [ -z "${WF_HEADER_DONE:-}" ] || return 0
  export WF_HEADER_DONE=1
  log "===== WarehouseFlow ${DEPLOY_MODE:-deploy}: ambiente=${WF_ENV:-?} tag=${TAG:-?} commit=${DEPLOY_SHA:-n/a} runner=${RUNNER_NAME:-$(hostname)} ====="
}

# Mantém só os 30 logs mais recentes deste ambiente (<env>-*.log); outros ambientes e arquivos
# com outro nome não são tocados.
prune_logs() {
  find "${STATE_DIR}/logs" -maxdepth 1 -name "${WF_ENV}-*.log" -type f -printf '%T@ %p\n' 2>/dev/null |
    sort -rn | tail -n +31 | cut -d' ' -f2- | xargs -r rm -f 2>/dev/null || true
}

# Copia a parte do log desta execução para ${STATE_DIR}/logs (fica na VM mesmo se o upload falhar).
# Grava uma única vez por processo; falha ao gravar só emite um AVISO em stderr (sem usar "log",
# que escreveria no próprio arquivo). Nunca altera o código de saída.
WF_LOG_PERSISTED="${WF_LOG_PERSISTED:-0}"
persist_log() {
  local dest
  [ "$WF_LOG_PERSISTED" != "1" ] || return 0
  if [ -z "${STATE_DIR:-}" ] || [ ! -d "${STATE_DIR}" ] || [ ! -f "${DEPLOY_LOG:-}" ]; then
    return 0
  fi
  WF_LOG_PERSISTED=1
  if ! mkdir -p "${STATE_DIR}/logs" 2>/dev/null; then
    printf 'AVISO: não foi possível criar %s/logs; o log desta execução não foi copiado para o servidor (o log do runner continua em %s)\n' \
      "$STATE_DIR" "$DEPLOY_LOG" >&2
    return 0
  fi
  dest="${STATE_DIR}/logs/${WF_ENV}-${DEPLOY_MODE:-deploy}-$(date -u +%Y%m%d-%H%M%S)-$$.log"
  if ! tail -c +"$((${WF_LOG_OFFSET:-0} + 1))" "$DEPLOY_LOG" > "$dest" 2>/dev/null; then
    rm -f "$dest" 2>/dev/null || true
    printf 'AVISO: não foi possível gravar %s; o log desta execução não foi copiado para o servidor\n' "$dest" >&2
    return 0
  fi
  chmod 600 "$dest" 2>/dev/null || true
  prune_logs
  return 0
}

# Para "trap on_exit EXIT": salva o log e sai SEMPRE com o código original, mesmo que a
# gravação do log falhe (set -e é desligado aqui para nenhum comando trocar o código de saída).
on_exit() {
  local rc=$?
  set +e
  persist_log
  exit "$rc"
}

http_base() {
  local port
  port="$(env_get HTTP_PORT "$ENV_FILE")"
  printf 'http://127.0.0.1:%s' "${port:-80}"
}

# Espera /health (com versão opcional) e /ready responderem 200.
wf_healthcheck() {
  local base="$1" expected="${2:-}" attempts="${3:-30}" i body
  for ((i = 1; i <= attempts; i++)); do
    if body="$(curl -fsS --max-time 5 "${base}/health" 2>/dev/null)" &&
      curl -fsS --max-time 5 -o /dev/null "${base}/ready" 2>/dev/null; then
      if [ -z "$expected" ] || printf '%s' "$body" | grep -Eq "\"version\": ?\"${expected}\""; then
        log "health OK em ${base}: ${body}"
        return 0
      fi
      log "versão diferente da esperada (${expected}) — tentativa ${i}/${attempts}: ${body}"
    else
      log "aguardando /health e /ready em ${base} — tentativa ${i}/${attempts}"
    fi
    sleep 5
  done
  return 1
}

record_history() {
  local tag="$1" result="$2"
  printf '%s\t%s\t%s\t%s\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$WF_ENV" "$tag" \
    "${DEPLOY_SHA:-manual}" "$result" >> "${STATE_DIR}/history.log"
}

# Container em execução de um serviço do projeto (pelos labels do Compose; não depende do env file).
service_container() {
  docker ps -q \
    --filter "label=com.docker.compose.project=${COMPOSE_PROJECT}" \
    --filter "label=com.docker.compose.service=$1" | head -n 1
}

# Marca as imagens em execução como :rollback-<ambiente> (ponto de retorno local).
save_rollback_point() {
  local service image_repo cid image_id saved=0
  for service in api frontend; do
    case "$service" in
      api) image_repo="warehouseflow-api" ;;
      frontend) image_repo="warehouseflow-nginx" ;;
    esac
    cid="$(service_container "$service")"
    if [ -z "$cid" ]; then
      log "sem container ${service} em execução — sem ponto de rollback para ele"
      continue
    fi
    image_id="$(docker inspect -f '{{.Image}}' "$cid")"
    WF_CACHE=1
    docker tag "$image_id" "${image_repo}:${ROLLBACK_TAG}"
    log "ponto de rollback: ${service} -> ${image_repo}:${ROLLBACK_TAG}"
    saved=$((saved + 1))
  done
  [ "$saved" -eq 2 ]
}

# Volta para as imagens :rollback-<ambiente>. Ajusta o env file para refletir o que está rodando.
# Retorna 1 em falha (chamado dentro de "if", onde set -e não vale).
rollback_local() {
  local version
  if ! docker image inspect "warehouseflow-api:${ROLLBACK_TAG}" >/dev/null 2>&1 ||
    ! docker image inspect "warehouseflow-nginx:${ROLLBACK_TAG}" >/dev/null 2>&1; then
    log "imagens de rollback (${ROLLBACK_TAG}) não existem neste servidor"
    return 1
  fi
  WF_CHANGED=1

  version="$(docker image inspect -f '{{index .Config.Labels "org.opencontainers.image.version"}}' \
    "warehouseflow-api:${ROLLBACK_TAG}" 2>/dev/null || true)"
  env_set API_IMAGE "warehouseflow-api" "$ENV_FILE" || return 1
  env_set NGINX_IMAGE "warehouseflow-nginx" "$ENV_FILE" || return 1
  env_set IMAGE_TAG "$ROLLBACK_TAG" "$ENV_FILE" || return 1
  if [ -n "$version" ] && [ "$version" != "<no value>" ]; then
    env_set APP_VERSION "$version" "$ENV_FILE" || return 1
  fi

  log "rollback: subindo warehouseflow-api/nginx:${ROLLBACK_TAG} (versão ${version:-desconhecida})"
  compose up -d --no-build --no-deps --wait --wait-timeout 180 api frontend || return 1
  wf_healthcheck "$(http_base)" "" 24
}
