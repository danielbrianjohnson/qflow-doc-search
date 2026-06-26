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
    echo "Starting Gunicorn (model loads on first request)..."
    exec gunicorn app.wsgi:application \
      --bind 0.0.0.0:8000 \
      --workers 2 \
      --timeout 120 \
      --access-logfile - \
      --error-logfile -
    ;;
  worker)
    echo "Starting Celery worker..."
    exec celery -A app worker --loglevel=info --concurrency=1
    ;;
  *)
    exec "$@"
    ;;
esac
