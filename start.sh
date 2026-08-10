#!/bin/bash
set -e

# Activate virtualenv if it exists in Railway build container
if [ -d "/app/.venv" ]; then
    source /app/.venv/bin/activate
fi

echo "==> Running Database Migrations..."
python manage.py migrate --noinput

echo "==> Collecting Static Files..."
python manage.py collectstatic --noinput

echo "==> Starting Daphne ASGI Web Server on Port ${PORT:-8000}..."
exec python -m daphne -b 0.0.0.0 -p ${PORT:-8000} chatappp.asgi:application
