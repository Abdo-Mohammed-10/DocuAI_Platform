#!/bin/bash
set -e

echo "⏳ Waiting for postgres..."
until pg_isready -h "${POSTGRES_HOST}" -U postgres; do
  sleep 1
done

echo "✅ Postgres ready. Running migrations..."
cd /app/shared
cd /app && alembic upgrade head

echo "✅ Migrations done. Starting service..."
exec "$@"