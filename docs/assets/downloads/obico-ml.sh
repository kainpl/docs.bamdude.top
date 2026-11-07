#!/usr/bin/env bash
# BamDude standalone Obico ML installer/updater. Version 1.
# Documentation: https://docs.bamdude.top/addons/obico-ml/
set -euo pipefail
umask 077

die() { printf 'Error: %s\n' "$*" >&2; exit 1; }
usage() {
  cat <<'HELP'
Usage:
  bash obico-ml.sh install [directory] [bind-IPv4] [port]
  bash obico-ml.sh {update|check|status|logs|token} [directory]

Defaults: $HOME/obico-ml, 127.0.0.1, 3333.
Install requires a NEW directory. Use a LAN IPv4 to reach ML from another host
or a BamDude container. 'token' explicitly prints the generated secret.
Update builds only ml_api, then replaces it; it never updates this script.
Check validates local configuration only (no fetch, build or restart).
Requires Linux, Bash, Docker with Compose v2, Git, curl, OpenSSL and flock.
HELP
}
action=${1:-help}
case "$action" in help|-h|--help) usage; exit 0 ;; esac
case "$action" in install|update|check|status|logs|token) ;; *) usage; exit 2 ;; esac
if [[ $action == install ]]; then
  (( $# <= 4 )) || die 'Too many arguments'
else
  (( $# <= 2 )) || die 'Too many arguments'
fi
for tool in docker git curl openssl flock realpath; do
  command -v "$tool" >/dev/null || die "Missing command: $tool"
done
root=$(realpath -m -- "${2:-$HOME/obico-ml}")
[[ $root != *$'\n'* && $root != *$'\r'* ]] || die 'Invalid directory'
upstream=https://github.com/TheSpaghettiDetective/obico-server.git

valid_address() {
  local octet
  local -a octets
  [[ $1 =~ ^[0-9]{1,3}(\.[0-9]{1,3}){3}$ ]] || return 1
  IFS=. read -r -a octets <<< "$1"
  for octet in "${octets[@]}"; do
    (( 10#$octet <= 255 )) || return 1
  done
  [[ $1 != 0.0.0.0 ]] # Explicit interface only, never all interfaces.
}
valid_port() { [[ $1 =~ ^[1-9][0-9]{0,4}$ ]] && (( $1 <= 65535 )); }

if [[ $action == install ]]; then
  bind=${3:-127.0.0.1}
  port=${4:-3333}
  valid_address "$bind" || die 'Use a specific IPv4 address (not 0.0.0.0)'
  valid_port "$port" || die 'Port must be between 1 and 65535'
  docker compose version >/dev/null
  docker info >/dev/null
  mkdir -p -- "$(dirname -- "$root")"
  mkdir -- "$root" || die 'Install needs a new directory; use update for an existing install'
else
  [[ -f $root/.bamdude-obico-ml ]] || die 'Not an installation made by this script'
fi
exec 9>"$root/.lock"
flock -n 9 || die 'Another operation is running in this directory'

if [[ $action == install ]]; then
  cp -- "${BASH_SOURCE[0]}" "$root/obico-ml.sh"
  token=$(openssl rand -hex 32)
  project="bamdude-obico-$(openssl rand -hex 6)"
  printf 'ML_BIND=%s\nML_PORT=%s\nML_TOKEN=%s\nML_PROJECT=%s\n' \
    "$bind" "$port" "$token" "$project" > "$root/.env"
  cat > "$root/compose.yaml" <<'COMPOSE'
services:
  ml_api:
    build:
      context: ./source/ml_api
    restart: unless-stopped
    ports:
      - "${ML_BIND:?}:${ML_PORT:?}:3333"
    environment:
      DEBUG: 'False'
      FLASK_APP: server.py
      ML_API_TOKEN: "${ML_TOKEN:?}"
    command: [gunicorn, --bind, '0.0.0.0:3333', --workers, '1', --timeout, '120', wsgi]
    healthcheck:
      test: [CMD-SHELL, 'wget -q -O - http://127.0.0.1:3333/hc/ | grep -qx ok']
      start_period: 140s
      interval: 10s
      timeout: 10s
      retries: 6
COMPOSE
  git clone --branch release --single-branch "$upstream" "$root/source"
  printf '1\n' > "$root/.bamdude-obico-ml"
fi

# Do not source the configuration: it is data, not shell code.
get_setting() {
  local value
  [[ $(grep -c "^$1=" "$root/.env") == 1 ]] || die "Missing or duplicate $1"
  value=$(sed -n "s/^$1=//p" "$root/.env")
  printf '%s' "$value"
}
bind=$(get_setting ML_BIND)
port=$(get_setting ML_PORT)
token=$(get_setting ML_TOKEN)
project=$(get_setting ML_PROJECT)
valid_address "$bind" || die 'Invalid ML_BIND in .env'
valid_port "$port" || die 'Invalid ML_PORT in .env'
[[ $token =~ ^[a-f0-9]{64}$ ]] || die 'Invalid ML_TOKEN in .env (expected 64 hex characters)'
[[ $project =~ ^bamdude-obico-[a-f0-9]{12}$ ]] || die 'Invalid ML_PROJECT in .env'
if [[ $action == token ]]; then printf '%s\n' "$token"; exit 0; fi

# The specified files and saved values take precedence over ambient Compose settings.
unset COMPOSE_FILE COMPOSE_PROFILES COMPOSE_PROJECT_NAME COMPOSE_ENV_FILES
unset ML_BIND ML_PORT ML_TOKEN ML_PROJECT
compose=(docker compose --project-directory "$root" --env-file "$root/.env"
  -p "$project" -f "$root/compose.yaml")
[[ $("${compose[@]}" config --services) == ml_api ]] || die 'Compose must contain only ml_api'
case "$action" in
  status) "${compose[@]}" ps ml_api; exit 0 ;;
  logs) "${compose[@]}" logs --tail 100 ml_api; exit 0 ;;
esac
[[ $(git -C "$root/source" remote get-url origin) == "$upstream" ]] || die 'Unexpected Git origin'
[[ $(git -C "$root/source" branch --show-current) == release ]] || die 'Expected release branch'
[[ -z $(git -C "$root/source" status --porcelain) ]] || die 'Source checkout has local changes'
if [[ $action == check ]]; then
  printf 'Configuration OK; no fetch, build or restart performed.\n'
  exit 0
fi
if [[ $action == update ]]; then
  git -C "$root/source" fetch origin release
  git -C "$root/source" merge --ff-only origin/release
fi
# A failed build leaves the running container intact. Do not stop it first.
"${compose[@]}" build --pull ml_api
"${compose[@]}" up -d --no-deps --no-build --wait --wait-timeout 300 ml_api
url="http://$bind:$port"
[[ $(curl --noproxy '*' -fsS --max-time 15 "$url/hc/") == ok ]] || die 'ML model is not ready'
code=$(curl --noproxy '*' -sS -o /dev/null -w '%{http_code}' --max-time 15 "$url/p/")
[[ $code == 401 ]] || die "Unauthenticated inference must return 401, got $code"
# Supply the bearer through stdin so it does not appear in curl's process arguments.
code=$(printf 'header = "Authorization: Bearer %s"\n' "$token" |
  curl --config - --noproxy '*' -sS -o /dev/null -w '%{http_code}' --max-time 15 "$url/p/")
[[ $code == 422 ]] || die "Authenticated inference without an image must return 422, got $code"
printf 'Obico ML ready at %s\nSource revision: ' "$url"
git -C "$root/source" rev-parse --short HEAD
printf 'Read your token with: bash %q token %q\n' "$root/obico-ml.sh" "$root"
