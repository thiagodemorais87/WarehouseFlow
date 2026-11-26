#!/usr/bin/env bash
# Valida /health (e a versão, se informada) e /ready.
# Uso: deploy/scripts/healthcheck.sh <base_url> [versao_esperada] [tentativas]
# Ex.: deploy/scripts/healthcheck.sh http://127.0.0.1 sha-abc1234 30
set -Eeuo pipefail

# shellcheck source=deploy/scripts/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

[ "$#" -ge 1 ] || {
  echo "uso: $0 <base_url> [versao_esperada] [tentativas]" >&2
  exit 2
}

if wf_healthcheck "$1" "${2:-}" "${3:-30}"; then
  exit 0
fi
die "health check falhou em $1"
