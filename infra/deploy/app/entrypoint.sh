#!/bin/sh

while ! nc -z "$POSTGRES_SERVER" "$POSTGRES_PORT"; do
  echo "Waiting for postgres to start..."
  sleep 3
done
echo 'Postgres started'

# alembic.ini лежит в /app/src (образ копирует ./src в /app/src)
cd /app/src && alembic upgrade head
cd /app

exec uvicorn src.main:app --host 0.0.0.0 --port 8000
