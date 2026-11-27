#!/usr/bin/env bash
# Rollback de staging ou production. Executado pelo workflow rollback.yml (runner self-hosted).
#
# Uso: deploy/scripts/rollback.sh <staging|production> [tag]
#   sem tag  volta para as imagens locais :rollback-<ambiente> (versão anterior ao último deploy)
#   com tag  implanta essa tag do GHCR (ex.: sha-abc1234) via deploy.sh, sem sincronizar o Git;
#            exige as mesmas variáveis do deploy.sh (inclusive a autenticação real no banco)
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=deploy/scripts/common.sh
source "${SCRIPT_DIR}/common.sh"

WF_ENV="${1:-}"
TAG="${2:-}"
DEPLOY_MODE="rollback"
export DEPLOY_LOG="${DEPLOY_LOG:-${RUNNER_TEMP:-/tmp}/rollback-${WF_ENV:-desconhecido}.log}"
mkdir -p "$(dirname "$DEPLOY_LOG")"
touch "$DEPLOY_LOG"
export WF_LOG_OFFSET="${WF_LOG_OFFSET:-$(wc -c < "$DEPLOY_LOG")}"
trap on_exit EXIT
log_header

phase "pré-checagem"
if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  die "uso: rollback.sh <staging|production> [tag]"
fi

if [ -n "$TAG" ]; then
  validate_tag "$TAG"
  log "rollback de ${WF_ENV} para a tag ${TAG} do registry (via deploy.sh)"
  # Quem preserva o log neste caminho é o deploy.sh (exec), que herda DEPLOY_LOG e WF_LOG_OFFSET:
  # um único arquivo por execução.
  trap - EXIT
  SKIP_GIT_SYNC=1 DEPLOY_MODE=rollback exec bash "${SCRIPT_DIR}/deploy.sh" "$WF_ENV" "$TAG"
fi

init_target
[ -f "$ENV_FILE" ] || die "${ENV_FILE} não existe: não há deploy anterior para reverter"

summary "### rollback — ${WF_ENV}"
summary ""
summary "- Destino: imagens locais \`:${ROLLBACK_TAG}\`"

cd "$DEPLOY_PATH"
phase "rollback para as imagens locais"
if rollback_local; then
  record_history "$ROLLBACK_TAG" "rollback-manual-ok"
  summary "- Resultado: **sucesso** (health e ready OK)"
  log "rollback de ${WF_ENV} concluído"
  exit 0
fi
record_history "$ROLLBACK_TAG" "rollback-manual-falhou"
die "rollback de ${WF_ENV} falhou: intervenção manual (docs/devops/rollback.md)"
