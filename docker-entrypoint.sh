#!/bin/sh
# Runtime entrypoint — runs as root just long enough to fix volume
# ownership, then drops to the `app` user via gosu.
#
# Why this exists:
#   Railway / Fly / Render mount the persistent volume on top of the
#   /app/data directory we chowned at build time, replacing ownership
#   with root:root. Without this script, the non-root `app` user can't
#   create chroma.sqlite3 or write uploads, and the server crashes on
#   first start with PermissionError.
set -e

mkdir -p /app/data/chroma /app/data/uploads
chown -R app:app /app/data 2>/dev/null || true

exec gosu app "$@"
