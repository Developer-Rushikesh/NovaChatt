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

echo "==> Running Database Migrations..."
python manage.py migrate --noinput || echo "Migration notice: proceeding with server start..."

echo "==> Collecting Static Files..."
python manage.py collectstatic --noinput || echo "Collectstatic notice: proceeding with server start..."

echo "==> Starting Daphne ASGI Web Server on 0.0.0.0:${PORT}..."
exec python -m daphne -b 0.0.0.0 -p "$PORT" --proxy-headers chatappp.asgi:application
