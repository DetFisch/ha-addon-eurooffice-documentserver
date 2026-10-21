#!/usr/bin/env bash

repair_persisted_owner() {
  local source="$1"
  local target="$2"
  local owner="$3"
  local protect_secrets="${4:-false}"
  local uid gid protected

  if [ ! -L "$source" ] || [ -L "$target" ] || [ ! -d "$target" ] ||
    [ "$(readlink -f -- "$source")" != "$(readlink -f -- "$target")" ]; then
    log "ERROR: refusing ownership repair for unexpected persistence mapping: $source -> $target."
    return 1
  fi

  if ! uid="$(id -u "$owner")" || ! gid="$(id -g "$owner")"; then
    log "ERROR: cannot resolve service account '$owner'."
    return 1
  fi

  log "Checking persisted ownership of $target for $owner ($uid:$gid)."

  # Operate on the real directory: recursive chown of the source symlink
  # changes the link only. Never follow symlinks inside persisted state.
  if [ "$protect_secrets" = "true" ]; then
    find -P "$target" -xdev \
      \( -path "$target/.private" -o -path "$target/wopi_private.key" -o -path "$target/wopi_public.key" \) -prune -o \
      \( ! -uid "$uid" -o ! -gid "$gid" \) -exec chown -h -- "$uid:$gid" {} + || return 1

    # Match the upstream entrypoint's root-only ownership of stored secrets.
    for protected in "$target/.private" "$target/wopi_private.key" "$target/wopi_public.key"; do
      if [ -e "$protected" ] || [ -L "$protected" ]; then
        find -P "$protected" -xdev \( ! -uid 0 -o ! -gid 0 \) \
          -exec chown -h -- 0:0 {} + || return 1
      fi
    done
  else
    find -P "$target" -xdev \( ! -uid "$uid" -o ! -gid "$gid" \) \
      -exec chown -h -- "$uid:$gid" {} + || return 1
  fi

  # Upstream checks the link with stat (without -L). Align it as well so it
  # does not repeatedly announce a repair of already-correct persisted data.
  if [ "$(stat -c '%u:%g' -- "$source")" != "$uid:$gid" ]; then
    chown -h -- "$uid:$gid" "$source" || return 1
  fi
}

persist_path() {
  local source="$1"
  local target="$2"
  local owner="$3"
  local protect_secrets="${4:-false}"

  mkdir -p "$(dirname "$source")" "$(dirname "$target")"

  if [ -L "$target" ] || { [ -e "$target" ] && [ ! -d "$target" ]; }; then
    log "ERROR: persistence target must be a real directory: $target."
    return 1
  fi
  if [ -L "$source" ] && [ "$(readlink -m -- "$source")" != "$(readlink -m -- "$target")" ]; then
    log "ERROR: persistence symlink points to an unexpected target: $source."
    return 1
  fi

  if [ ! -e "$target" ]; then
    mkdir -p "$target"
    if [ -d "$source" ] && [ ! -L "$source" ]; then
      cp -a "${source}/." "$target/" 2>/dev/null || true
      chown --reference="$source" "$target" 2>/dev/null || true
      chmod --reference="$source" "$target" 2>/dev/null || true
    fi
  fi

  if [ ! -L "$source" ]; then
    if [ -e "$source" ]; then
      rm -rf "$source"
    fi
    ln -s "$target" "$source"
  fi

  repair_persisted_owner "$source" "$target" "$owner" "$protect_secrets"
}
