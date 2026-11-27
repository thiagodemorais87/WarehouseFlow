#!/usr/bin/env bash
# Operações no GHCR com novas tentativas para falhas de rede. Ver docs/devops/ci-cd.md.
#
# Uso:
#   deploy/scripts/ghcr.sh login                        requer GHCR_USER e GHCR_TOKEN (lido do ambiente)
#   deploy/scripts/ghcr.sh retry <descrição> <cmd...>   ex.: retry "push api" docker push img:tag
#   deploy/scripts/ghcr.sh exists <imagem:tag>          ver códigos abaixo
#
# Classificação da saída do docker (ordem: local, auth, notfound, network, other):
#   local     docker inacessível/sem permissão no socket do runner  -> falha na hora (rc 5)
#   auth      401/403, unauthorized, denied...                       -> falha na hora (rc 3)
#   notfound  404, manifest unknown...                               -> falha na hora (rc 4); em "exists" = 2
#   network   timeout, 502/503/504, conexão...                       -> novas tentativas com espera exponencial
#   other     qualquer outra coisa                                   -> novas tentativas, mostrando a saída
# Códigos de "exists": 0 existe, 2 inexistente, 3 auth, 5 local, 1 rede esgotada ou erro desconhecido
# (erro nunca é tratado como "imagem ausente").
# Também pode ser carregado com "source" (deploy.sh usa ghcr_retry).
set -Eeuo pipefail

GHCR_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=deploy/scripts/common.sh
source "${GHCR_SCRIPT_DIR}/common.sh"

GHCR_REGISTRY="${GHCR_REGISTRY:-ghcr.io}"
GHCR_ATTEMPTS="${GHCR_ATTEMPTS:-5}"
GHCR_BACKOFF="${GHCR_BACKOFF:-5}"
GHCR_LOGIN_TIMEOUT="${GHCR_LOGIN_TIMEOUT:-60}"
GHCR_CMD_TIMEOUT="${GHCR_CMD_TIMEOUT:-900}"

# Códigos HTTP só casam como token isolado: "ab401cd" (trecho de digest) não é HTTP 401.
GHCR_B='(^|[^[:alnum:]])'
GHCR_E='([^[:alnum:]]|$)'
GHCR_LOCAL_RE='permission denied.*docker\.sock|cannot connect to the docker daemon|is the docker daemon running'
GHCR_AUTH_RE="unauthorized|authentication required|incorrect username or password|requested access to the resource is denied|denied: |permission_denied|insufficient_scope|forbidden|${GHCR_B}40[13]${GHCR_E}"
GHCR_NOTFOUND_RE="manifest unknown|name unknown|no such manifest|manifest.*not found|${GHCR_B}404${GHCR_E}"
GHCR_NETWORK_RE="deadline exceeded|client\.timeout|i/o timeout|tls handshake timeout|timed out|timeout expired|connection (reset|refused|closed)|no such host|temporary failure|network is unreachable|no route to host|bad gateway|service unavailable|gateway time-?out|${GHCR_B}eof${GHCR_E}|${GHCR_B}50[234]${GHCR_E}"

# local | auth | notfound | network | other, a partir do código de saída e da saída do comando.
ghcr_classify() {
  local rc="$1" out="$2"
  if grep -Eqi "$GHCR_LOCAL_RE" <<<"$out"; then
    echo local
  elif grep -Eqi "$GHCR_AUTH_RE" <<<"$out"; then
    echo auth
  elif grep -Eqi "$GHCR_NOTFOUND_RE" <<<"$out"; then
    echo notfound
  elif [ "$rc" -eq 124 ] || grep -Eqi "$GHCR_NETWORK_RE" <<<"$out"; then
    echo network
  else
    echo other
  fi
}

ghcr_last_line() {
  local line
  line="$(printf '%s\n' "$1" | sed '/^[[:space:]]*$/d' | tail -n 1)"
  printf '%s' "${line:0:300}"
}

# Executa uma tentativa. Define GHCR_OUT e devolve o código de saída do comando.
ghcr_attempt() {
  local kind="$1"
  shift
  local rc=0
  if [ "$kind" = "login" ]; then
    GHCR_OUT="$(printf '%s' "$GHCR_TOKEN" |
      timeout "$GHCR_LOGIN_TIMEOUT" docker login "$GHCR_REGISTRY" -u "$GHCR_USER" --password-stdin 2>&1)" || rc=$?
  else
    GHCR_OUT="$(timeout "$GHCR_CMD_TIMEOUT" "$@" 2>&1)" || rc=$?
  fi
  return "$rc"
}

# Laço de novas tentativas. Devolve 0 (ok), 3 (credencial/permissão), 4 (não existe),
# 5 (docker local) ou 1 (esgotou as tentativas / erro).
ghcr_run() {
  local desc="$1" kind="$2"
  shift 2
  local attempt=1 delay="$GHCR_BACKOFF" rc class reason
  while :; do
    rc=0
    ghcr_attempt "$kind" "$@" || rc=$?
    if [ "$rc" -eq 0 ]; then
      if [ "$attempt" -gt 1 ]; then
        log "${desc}: ok na tentativa ${attempt}/${GHCR_ATTEMPTS}"
      else
        log "${desc}: ok"
      fi
      return 0
    fi
    class="$(ghcr_classify "$rc" "$GHCR_OUT")"
    case "$class" in
      local)
        log "ERRO: ${desc}: o Docker do runner não está acessível (não é problema do registry): $(ghcr_last_line "$GHCR_OUT")"
        return 5
        ;;
      auth)
        log "ERRO: ${desc}: o GHCR recusou a credencial ou a permissão (não é timeout de rede): $(ghcr_last_line "$GHCR_OUT")"
        log "confira 'permissions: packages' no job e, em github.com → Packages → <pacote> → Package settings, o acesso do repositório ao pacote"
        return 3
        ;;
      notfound)
        log "ERRO: ${desc}: a imagem/tag não existe no registry (não é timeout de rede): $(ghcr_last_line "$GHCR_OUT")"
        return 4
        ;;
      network) reason="timeout/erro de rede" ;;
      *) reason="erro não classificado" ;;
    esac
    if [ "$attempt" -ge "$GHCR_ATTEMPTS" ]; then
      log "ERRO: ${desc}: falhou após ${GHCR_ATTEMPTS} tentativas (${reason}, código ${rc}). Saída da última tentativa:"
      log "$(printf '%s\n' "$GHCR_OUT" | tail -n 20)"
      return 1
    fi
    log "${desc}: tentativa ${attempt}/${GHCR_ATTEMPTS} falhou (${reason}): $(ghcr_last_line "$GHCR_OUT") — nova tentativa em ${delay}s"
    sleep "$delay"
    delay=$((delay * 2))
    attempt=$((attempt + 1))
  done
}

ghcr_login() {
  require_vars GHCR_USER GHCR_TOKEN
  ghcr_run "login em ${GHCR_REGISTRY}" login
}

ghcr_retry() {
  local desc="$1"
  shift
  [ "$#" -gt 0 ] || die "ghcr_retry: comando ausente"
  ghcr_run "$desc" cmd "$@"
}

# 0 = publicada; 2 = manifest inexistente; 3 = auth/permissão; 5 = docker local;
# 1 = rede esgotada ou erro desconhecido (nunca confundido com "ausente").
ghcr_exists() {
  local ref="$1" attempt=1 delay="$GHCR_BACKOFF" rc class
  while :; do
    rc=0
    ghcr_attempt cmd docker manifest inspect "$ref" || rc=$?
    if [ "$rc" -eq 0 ]; then
      log "${ref}: já publicada no registry"
      return 0
    fi
    class="$(ghcr_classify "$rc" "$GHCR_OUT")"
    case "$class" in
      notfound)
        log "${ref}: ainda não publicada (manifest inexistente)"
        return 2
        ;;
      auth)
        log "ERRO: ${ref}: o GHCR recusou a credencial ou a permissão ao consultar a imagem — isto NÃO significa imagem ausente: $(ghcr_last_line "$GHCR_OUT")"
        return 3
        ;;
      local)
        log "ERRO: ${ref}: o Docker do runner não está acessível — isto NÃO significa imagem ausente: $(ghcr_last_line "$GHCR_OUT")"
        return 5
        ;;
      network)
        if [ "$attempt" -lt "$GHCR_ATTEMPTS" ]; then
          log "${ref}: consulta falhou (timeout/erro de rede), tentativa ${attempt}/${GHCR_ATTEMPTS} — nova tentativa em ${delay}s"
          sleep "$delay"
          delay=$((delay * 2))
          attempt=$((attempt + 1))
          continue
        fi
        log "ERRO: ${ref}: não foi possível confirmar se existe após ${GHCR_ATTEMPTS} tentativas (timeout/erro de rede) — NÃO tratado como imagem ausente: $(ghcr_last_line "$GHCR_OUT")"
        return 1
        ;;
      *)
        log "ERRO: ${ref}: resposta inesperada ao consultar a imagem (código ${rc}) — NÃO tratada como imagem ausente: $(ghcr_last_line "$GHCR_OUT")"
        return 1
        ;;
    esac
  done
}

ghcr_main() {
  local cmd="${1:-}"
  [ "$#" -gt 0 ] && shift
  case "$cmd" in
    login) ghcr_login ;;
    retry)
      [ "$#" -ge 2 ] || die "uso: ghcr.sh retry <descrição> <comando...>"
      ghcr_retry "$@"
      ;;
    exists)
      [ "$#" -eq 1 ] || die "uso: ghcr.sh exists <imagem:tag>"
      ghcr_exists "$1"
      ;;
    *)
      echo "uso: $0 login | retry <descrição> <comando...> | exists <imagem:tag>" >&2
      return 64
      ;;
  esac
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  ghcr_main "$@"
fi
