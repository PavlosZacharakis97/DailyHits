#!/bin/sh
# Container entrypoint: wait for Postgres, apply migrations, optionally collect
# static files, then exec the CMD (runserver in dev, gunicorn in prod).
set -eu

python - <<'PY'
import os
import sys
import time

import psycopg

url = os.environ["DATABASE_URL"]
timeout = int(os.environ.get("DB_WAIT_TIMEOUT", "60"))
deadline = time.monotonic() + timeout
while True:
    try:
        psycopg.connect(url, connect_timeout=3).close()
        break
    except psycopg.OperationalError as exc:
        if time.monotonic() > deadline:
            sys.exit(f"Database is not reachable after {timeout}s: {exc}")
        print("Waiting for database...", flush=True)
        time.sleep(1)
PY

if [ "${DJANGO_MIGRATE:-1}" = "1" ]; then
    python manage.py migrate --noinput
fi

if [ "${DJANGO_COLLECTSTATIC:-0}" = "1" ]; then
    python manage.py collectstatic --noinput
fi

exec "$@"
