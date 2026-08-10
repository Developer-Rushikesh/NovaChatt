#!/bin/bash
set -e

# Find and activate Python virtual environment in Railway container
if [ -d "/app/.venv" ]; then
    source /app/.venv/bin/activate
elif [ -d "/venv" ]; then
    source /venv/bin/activate
fi

# Ensure PORT env is defined (defaults to 8000 if not set)
PORT="${PORT:-8000}"

# Fail fast and loudly if DATABASE_URL is not configured in a non-DEBUG environment,
# instead of silently falling back to SQLite while allauth expects PostgreSQL.
if [ -z "${DATABASE_URL}" ] && [ "$(echo "${DEBUG:-False}" | tr '[:upper:]' '[:lower:]')" != "true" ]; then
    echo "WARNING: DATABASE_URL is not set. Falling back to SQLite for this run."
    echo "If a PostgreSQL service is attached on Railway, make sure DATABASE_URL is referenced in this service's Variables tab."
fi

echo "==> Waiting for database to become available..."
python - <<'PYEOF'
import os
import sys
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chatappp.settings")

import django
django.setup()

from django.db import connections
from django.db.utils import OperationalError

max_retries = 30
delay_seconds = 2

for attempt in range(1, max_retries + 1):
    try:
        connections["default"].ensure_connection()
        print("Database connection established.")
        break
    except OperationalError as exc:
        print(f"Database not ready yet (attempt {attempt}/{max_retries}): {exc}")
        if attempt == max_retries:
            print("Database never became available. Exiting so Railway can restart the deploy.")
            sys.exit(1)
        time.sleep(delay_seconds)
PYEOF

echo "==> Running Database Migrations..."
python manage.py migrate --noinput

echo "==> Collecting Static Files..."
python manage.py collectstatic --noinput

echo "==> Starting Daphne ASGI Web Server on 0.0.0.0:${PORT}..."
exec python -m daphne -b 0.0.0.0 -p "$PORT" --proxy-headers chatappp.asgi:application
