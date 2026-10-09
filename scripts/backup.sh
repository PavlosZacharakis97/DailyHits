#!/usr/bin/env bash
# Back up the database: pg_dump from the db container, compressed custom format,
# keeping the newest $BACKUP_KEEP files (default 14) in backups/.
#
#   scripts/backup.sh                                   # dev stack
#   COMPOSE_FILE=docker-compose.prod.yml scripts/backup.sh   # prod stack
#
# Schedule it with cron, e.g. every night at 03:00:
#   0 3 * * * cd /path/to/DailyHit.live && scripts/backup.sh >> backups/backup.log 2>&1
set -euo pipefail

cd "$(dirname "$0")/.."
KEEP="${BACKUP_KEEP:-14}"
DIR="${BACKUP_DIR:-backups}"
mkdir -p "$DIR"

stamp="$(date -u +%Y%m%d-%H%M%S)"
file="$DIR/dailyhit-$stamp.dump"
tmp="$file.partial"
trap 'rm -f "$tmp"' EXIT

# The credentials live inside the db container (POSTGRES_USER / POSTGRES_DB),
# so nothing secret appears on this command line.
docker compose exec -T db sh -c 'pg_dump --format=custom --compress=9 --no-owner -U "$POSTGRES_USER" -d "$POSTGRES_DB"' > "$tmp"

# A dump we cannot list is useless: check it before keeping it.
docker compose exec -T db pg_restore --list < "$tmp" > /dev/null
mv "$tmp" "$file"
echo "Backup written: $file ($(du -h "$file" | cut -f1))"

# Rotation: keep the newest $KEEP dumps.
ls -1t "$DIR"/dailyhit-*.dump 2>/dev/null | tail -n +"$((KEEP + 1))" | while read -r old; do
  rm -f -- "$old"
  echo "Removed old backup: $old"
done
