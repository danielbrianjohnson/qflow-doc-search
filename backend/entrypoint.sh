#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
until python -c "
import os, psycopg2
conn = psycopg2.connect(os.environ['DATABASE_URL'])
conn.close()
" 2>/dev/null; do
  sleep 1
done
echo "PostgreSQL is ready."

case "$1" in
  web)
    echo "Running database migrations..."
    python manage.py migrate --noinput
    echo "Starting Django server (model loads on first request)..."
    exec python manage.py runserver 0.0.0.0:8000
    ;;
  worker)
    echo "Starting Celery worker..."
    exec celery -A app worker --loglevel=info --concurrency=1
    ;;
  *)
    exec "$@"
    ;;
esac
