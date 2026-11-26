#!/usr/bin/env bash
# Funções compartilhadas por deploy.sh, rollback.sh e healthcheck.sh.
# Uso: source "$(dirname "$0")/common.sh"

log() {
  local line
  line="[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"
  printf '%s\n' "$line" >&2
  if [ -n "${DEPLOY_LOG:-}" ]; then
    printf '%s\n' "$line" >> "$DEPLOY_LOG"
  fi
}

die() {
  log "ERRO: $*"
  summary "**Falha:** $*"
  exit 1
}

summary() {
  if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
    printf '%s\n' "$*" >> "$GITHUB_STEP_SUMMARY"
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

# Lê KEY=valor de um env file (remove aspas simples/duplas externas).
env_get() {
  local key="$1" file="$2" line
  [ -f "$file" ] || return 0
  line="$(grep -E "^${key}=" "$file" | tail -n 1 || true)"
  line="${line#*=}"
  line="${line#\'}"
  line="${line%\'}"
  line="${line#\"}"
  line="${line%\"}"
  printf '%s' "$line"
}

# Define KEY='valor' num env file, preservando as demais linhas e a permissão 600.
env_set() {
  local key="$1" value="$2" file="$3" tmp
  tmp="$(mktemp "${STATE_DIR}/env.XXXXXX")"
  chmod 600 "$tmp"
  grep -vE "^${key}=" "$file" > "$tmp" || true
  printf "%s='%s'\n" "$key" "$value" >> "$tmp"
  mv "$tmp" "$file"
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
