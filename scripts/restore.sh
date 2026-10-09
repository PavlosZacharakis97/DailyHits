#!/usr/bin/env bash
# Restore the database from a dump made by scripts/backup.sh.
# THIS REPLACES ALL CURRENT DATA. The backend is stopped while restoring.
#
#   scripts/restore.sh backups/dailyhit-20261009-030000.dump
set -euo pipefail

cd "$(dirname "$0")/.."
dump="${1:-}"
if [[ -z "$dump" || ! -f "$dump" ]]; then
  echo "Usage: scripts/restore.sh backups/dailyhit-YYYYMMDD-HHMMSS.dump" >&2
  echo "Available backups:" >&2
  ls -1t backups/dailyhit-*.dump 2>/dev/null >&2 || echo "  (none)" >&2
  exit 1
fi

db_name="$(docker compose exec -T db sh -c 'printf %s "$POSTGRES_DB"')"
echo "This will REPLACE every table in the database “$db_name” with $dump."
read -r -p "Type the database name to continue: " answer
if [[ "$answer" != "$db_name" ]]; then
  echo "Cancelled." >&2
  exit 1
fi

docker compose stop backend
trap 'docker compose start backend' EXIT
docker compose exec -T db sh -c 'pg_restore --clean --if-exists --no-owner --single-transaction -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < "$dump"
echo "Restored $dump."
