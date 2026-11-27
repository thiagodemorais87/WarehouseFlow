#!/usr/bin/env bash
# Deploy de uma tag de imagem do GHCR em staging ou production.
# Executado pelo runner self-hosted (workflow ci-cd.yml / rollback.yml). Ver docs/devops/ci-cd.md.
#
# Uso: deploy/scripts/deploy.sh <staging|production> <tag>
#
# Variáveis de ambiente:
#   obrigatórias  DEPLOY_PATH, API_IMAGE, NGINX_IMAGE,
#                 POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, SECRET_KEY
#   opcionais     DEPLOY_SHA + DEPLOY_BRANCH (sincroniza o clone Git do servidor), SKIP_GIT_SYNC=1,
#                 APP_ENV, HTTP_PORT, COOKIE_SECURE, ENABLE_DOCS, DEPLOY_LOG,
#                 BACKUP_DB=true|false (sempre true em production), DEPLOY_MODE=deploy|rollback
#
# Etapas:
#   pré-checagem (argumentos, diretório, Secrets) -> autenticação real no banco -> download das imagens
#   -> Git -> backup do banco -> ponto de rollback -> .env -> up -> health.
# Até o download das imagens nada é alterado no servidor; qualquer falha ali interrompe o deploy.
# Se up/health falhar: restaura o .env anterior e as imagens :rollback-<ambiente>.
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=deploy/scripts/common.sh
source "${SCRIPT_DIR}/common.sh"
# shellcheck source=deploy/scripts/ghcr.sh
source "${SCRIPT_DIR}/ghcr.sh"

WF_ENV="${1:-}"
TAG="${2:-}"
DEPLOY_MODE="${DEPLOY_MODE:-deploy}"
export DEPLOY_LOG="${DEPLOY_LOG:-${RUNNER_TEMP:-/tmp}/deploy-${WF_ENV:-desconhecido}.log}"
mkdir -p "$(dirname "$DEPLOY_LOG")"
touch "$DEPLOY_LOG"
export WF_LOG_OFFSET="${WF_LOG_OFFSET:-$(wc -c < "$DEPLOY_LOG")}"
trap on_exit EXIT
log_header

phase "pré-checagem"
[ "$#" -eq 2 ] || die "uso: deploy.sh <staging|production> <tag>"
validate_tag "$TAG"
init_target
require_vars API_IMAGE NGINX_IMAGE POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB SECRET_KEY

summary "### ${DEPLOY_MODE} — ${WF_ENV}"
summary ""
summary "- Tag: \`${TAG}\`"
summary "- Imagens: \`${API_IMAGE}\`, \`${NGINX_IMAGE}\`"
summary "- Commit: \`${DEPLOY_SHA:-n/a}\`"

for name in POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB SECRET_KEY; do
  check_value "$name" secret
done
for name in API_IMAGE NGINX_IMAGE APP_ENV HTTP_PORT COOKIE_SECURE ENABLE_DOCS; do
  if [ -n "${!name:-}" ]; then
    check_value "$name"
  fi
done
WF_PASSWORD_URLENC="$(urlencode "$POSTGRES_PASSWORD")"

if [ "$WF_ENV" = "production" ]; then
  BACKUP_DB=true
fi

cd "$DEPLOY_PATH"
log "${DEPLOY_MODE} de ${TAG} em ${WF_ENV} (${DEPLOY_PATH})"

phase "autenticação no banco"
check_db_auth

phase "download das imagens"
# Mesmo um pull que falha pela metade pode ter baixado camadas para o cache local do Docker.
WF_CACHE=1
for image in "$API_IMAGE" "$NGINX_IMAGE"; do
  ghcr_retry "download ${image}:${TAG}" docker pull --quiet "${image}:${TAG}" ||
    die "não foi possível baixar ${image}:${TAG} do registry"
done

sync_git() {
  if [ "${SKIP_GIT_SYNC:-0}" = "1" ] || [ -z "${DEPLOY_SHA:-}" ]; then
    log "sincronização do Git ignorada"
    return 0
  fi
  require_vars DEPLOY_BRANCH
  local current
  current="$(git rev-parse --abbrev-ref HEAD)"
  [ "$current" = "$DEPLOY_BRANCH" ] ||
    die "o clone em ${DEPLOY_PATH} está no branch '${current}', esperado '${DEPLOY_BRANCH}'"
  git fetch --quiet origin "$DEPLOY_BRANCH"
  if git merge-base --is-ancestor "$DEPLOY_SHA" HEAD; then
    log "Git do servidor já contém ${DEPLOY_SHA}"
    return 0
  fi
  WF_CHANGED=1
  git merge --ff-only --quiet "$DEPLOY_SHA" ||
    die "não foi possível avançar '${DEPLOY_BRANCH}' até ${DEPLOY_SHA} só com fast-forward (há commits ou alterações locais no servidor)"
  log "Git do servidor em $(git rev-parse --short HEAD)"
}

backup_db() {
  if [ "${BACKUP_DB:-false}" != "true" ]; then
    log "backup do banco desativado (BACKUP_DB=${BACKUP_DB:-false})"
    return 0
  fi
  local cid file
  cid="$(service_container db)"
  if [ -z "$cid" ]; then
    log "banco ainda não está em execução — nada para salvar"
    return 0
  fi
  WF_CHANGED=1
  mkdir -p "${DEPLOY_PATH}/backups"
  file="${DEPLOY_PATH}/backups/${WF_ENV}-predeploy-$(date -u +%Y%m%d-%H%M%S).dump"
  # As variáveis são expandidas dentro do container (credenciais do próprio serviço db).
  # shellcheck disable=SC2016
  docker exec "$cid" sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/wf-predeploy.dump' ||
    die "pg_dump falhou: deploy abortado antes de alterar os serviços"
  docker cp "${cid}:/tmp/wf-predeploy.dump" "$file" ||
    die "não foi possível copiar o backup do banco: deploy abortado antes de alterar os serviços"
  docker exec "$cid" rm -f /tmp/wf-predeploy.dump || true
  chmod 600 "$file"
  log "backup do banco: ${file} ($(du -h "$file" | cut -f1))"
  summary "- Backup do banco: \`backups/$(basename "$file")\`"
}

write_env_file() {
  local tmp db_url
  tmp="$(mktemp "${STATE_DIR}/env.XXXXXX")"
  chmod 600 "$tmp"
  db_url="postgresql+psycopg2://$(urlencode "$POSTGRES_USER"):${WF_PASSWORD_URLENC}@db:5432/$(urlencode "$POSTGRES_DB")"
  {
    echo "# Gerado por deploy/scripts/deploy.sh em $(date -u +%Y-%m-%dT%H:%M:%SZ)."
    echo "# Não edite à mão: altere os Secrets/Variables do environment '${WF_ENV}' no GitHub."
    printf 'APP_ENV=%s\n' "$(env_quote "${APP_ENV:-$WF_ENV}")"
    printf 'APP_VERSION=%s\n' "$(env_quote "$TAG")"
    printf 'POSTGRES_USER=%s\n' "$(env_quote "$POSTGRES_USER")"
    printf 'POSTGRES_PASSWORD=%s\n' "$(env_quote "$POSTGRES_PASSWORD")"
    printf 'POSTGRES_DB=%s\n' "$(env_quote "$POSTGRES_DB")"
    printf 'DATABASE_URL=%s\n' "$(env_quote "$db_url")"
    printf 'SECRET_KEY=%s\n' "$(env_quote "$SECRET_KEY")"
    printf 'COOKIE_SECURE=%s\n' "$(env_quote "${COOKIE_SECURE:-false}")"
    printf 'ENABLE_DOCS=%s\n' "$(env_quote "${ENABLE_DOCS:-false}")"
    printf 'HTTP_PORT=%s\n' "$(env_quote "${HTTP_PORT:-80}")"
    printf 'API_IMAGE=%s\n' "$(env_quote "$API_IMAGE")"
    printf 'NGINX_IMAGE=%s\n' "$(env_quote "$NGINX_IMAGE")"
    printf 'IMAGE_TAG=%s\n' "$(env_quote "$TAG")"
  } > "$tmp"

  ENV_BACKUP=""
  if [ -f "$ENV_FILE" ]; then
    ENV_BACKUP="${STATE_DIR}/backups/.env.${WF_ENV}.$(date -u +%Y%m%d-%H%M%S)"
    cp -p "$ENV_FILE" "$ENV_BACKUP"
    chmod 600 "$ENV_BACKUP"
    log "env anterior salvo em ${ENV_BACKUP}"
  fi
  WF_CHANGED=1
  mv "$tmp" "$ENV_FILE"
  log "env gerado: ${ENV_FILE} (conteúdo não exibido)"

  # Mantém só os 20 backups de env mais recentes deste ambiente.
  find "${STATE_DIR}/backups" -maxdepth 1 -name ".env.${WF_ENV}.*" -type f -printf '%T@ %p\n' |
    sort -rn | tail -n +21 | cut -d' ' -f2- | xargs -r rm -f
}

# Retorna 1 em falha (chamada dentro de "if", onde set -e não vale).
# As imagens já foram baixadas na fase "download das imagens".
apply_release() {
  WF_CHANGED=1
  if [ -z "$(service_container db)" ]; then
    log "banco não está em execução — criando o serviço db"
    compose up -d --no-build --wait --wait-timeout 180 db || return 1
  fi
  compose up -d --no-build --no-deps --wait --wait-timeout 180 api frontend || return 1
  wf_healthcheck "$(http_base)" "$TAG" 30
}

phase "sincronização do Git"
sync_git

phase "backup do banco"
backup_db

phase "ponto de rollback"
HAS_ROLLBACK_POINT=0
if save_rollback_point; then
  HAS_ROLLBACK_POINT=1
fi

phase "arquivo .env"
write_env_file

phase "atualização dos serviços"
if apply_release; then
  record_history "$TAG" "ok"
  summary "- Resultado: **sucesso** (health e ready OK, versão \`${TAG}\`)"
  log "${DEPLOY_MODE} de ${TAG} em ${WF_ENV} concluído"
  exit 0
fi

phase "rollback automático"
log "${DEPLOY_MODE} de ${TAG} falhou — iniciando rollback automático"
record_history "$TAG" "falhou"
compose logs --no-color --tail 100 api frontend 2>&1 | while IFS= read -r line; do log "  $line"; done || true

if [ -n "${ENV_BACKUP:-}" ]; then
  cp -p "$ENV_BACKUP" "$ENV_FILE"
  log "env anterior restaurado"
fi

if [ "$HAS_ROLLBACK_POINT" != "1" ]; then
  die "${DEPLOY_MODE} de ${TAG} falhou e não havia versão anterior em execução para rollback"
fi

if rollback_local; then
  record_history "$ROLLBACK_TAG" "rollback-automatico-ok"
  die "${DEPLOY_MODE} de ${TAG} falhou; rollback automático para a versão anterior concluído (health OK)"
fi
record_history "$ROLLBACK_TAG" "rollback-automatico-falhou"
die "${DEPLOY_MODE} de ${TAG} falhou e o rollback automático também falhou: intervenção manual (docs/devops/rollback.md)"
