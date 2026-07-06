#!/usr/bin/env bash
set -Eeuo pipefail

CONFIG_PATH=/data/options.json
PERSIST_ROOT=/data/euro-office
EO_CONF_DIR="${EO_CONF:-/etc/euro-office/documentserver}"

log() {
  printf '[eurooffice-ha] %s\n' "$*"
}

config_has() {
  local key="$1"
  [ -f "$CONFIG_PATH" ] && jq -e --arg key "$key" 'has($key) and .[$key] != null' "$CONFIG_PATH" >/dev/null
}

config_string() {
  local key="$1"
  local default="${2:-}"

  if config_has "$key"; then
    jq -er --arg key "$key" '.[$key] // empty' "$CONFIG_PATH"
  else
    printf '%s' "$default"
  fi
}

config_bool() {
  local key="$1"
  local default="$2"

  if config_has "$key"; then
    jq -r --arg key "$key" 'if .[$key] == true then "true" else "false" end' "$CONFIG_PATH"
  else
    printf '%s' "$default"
  fi
}

validate_port() {
  local value="$1"

  if [[ ! "$value" =~ ^[0-9]+$ ]] || [ "$value" -lt 1 ] || [ "$value" -gt 65535 ]; then
    log "ERROR: portnumber must be between 1 and 65535, got '$value'."
    exit 1
  fi
}

configure_http_port() {
  local port="$1"
  local nginx_ds_conf="${EO_CONF_DIR}/nginx/ds.conf"

  if [ ! -f "$nginx_ds_conf" ]; then
    log "ERROR: nginx config not found at $nginx_ds_conf."
    exit 1
  fi

  sed -ri "s/listen 0\\.0\\.0\\.0:[0-9]+;/listen 0.0.0.0:${port};/" "$nginx_ds_conf"
  sed -ri "s/listen \\[::\\]:[0-9]+ default_server;/listen [::]:${port} default_server;/" "$nginx_ds_conf"
  sed -ri "s/listen \\[::\\]:[0-9]+;/listen [::]:${port};/" "$nginx_ds_conf"

  # The upstream entrypoint writes this value later when the example app is enabled.
  sed -i "s#http://localhost/example/#http://localhost:${port}/example/#g" /entrypoint.sh

  rm -f /etc/nginx/sites-enabled/default /etc/nginx/conf.d/default.conf 2>/dev/null || true
}

persist_path() {
  local source="$1"
  local target="$2"

  mkdir -p "$(dirname "$source")" "$(dirname "$target")"

  if [ ! -e "$target" ]; then
    mkdir -p "$target"
    if [ -d "$source" ] && [ ! -L "$source" ]; then
      cp -a "${source}/." "$target/" 2>/dev/null || true
      chown --reference="$source" "$target" 2>/dev/null || true
      chmod --reference="$source" "$target" 2>/dev/null || true
    fi
  fi

  if [ -L "$source" ]; then
    return
  fi

  if [ -e "$source" ]; then
    rm -rf "$source"
  fi

  ln -s "$target" "$source"
}

mkdir -p "$PERSIST_ROOT"

persist_path /var/www/euro-office/Data "$PERSIST_ROOT/Data"
persist_path /var/lib/euro-office/documentserver "$PERSIST_ROOT/lib-documentserver"
persist_path /var/log/euro-office/documentserver "$PERSIST_ROOT/logs"
persist_path /var/lib/postgresql "$PERSIST_ROOT/postgresql"
persist_path /var/lib/redis "$PERSIST_ROOT/redis"
persist_path /var/lib/rabbitmq "$PERSIST_ROOT/rabbitmq"

PORTNUMBER="$(config_string portnumber 8080)"
validate_port "$PORTNUMBER"
configure_http_port "$PORTNUMBER"

export JWT_ENABLED="$(config_bool jwt_enabled true)"
export JWT_HEADER="$(config_string jwt_header Authorization)"
export EXAMPLE_ENABLED="$(config_bool example_enabled false)"
export WOPI_ENABLED="$(config_bool wopi_enabled false)"
export ALLOW_PRIVATE_IP_ADDRESS="$(config_bool allow_private_ip_address false)"
export GENERATE_FONTS="$(config_bool generate_fonts true)"
export NGINX_WORKER_PROCESSES="$(config_string nginx_worker_processes 1)"

JWT_SECRET_VALUE="$(config_string jwt_secret)"
if [ -n "$JWT_SECRET_VALUE" ]; then
  export JWT_SECRET="$JWT_SECRET_VALUE"
  if [ "${#JWT_SECRET_VALUE}" -lt 32 ]; then
    log "WARNING: jwt_secret should be at least 32 characters for Nextcloud/HS256 integrations."
  fi
fi

log "Starting Euro-Office Document Server on port $PORTNUMBER."
log "Persistent data root: $PERSIST_ROOT"

exec /entrypoint.sh
