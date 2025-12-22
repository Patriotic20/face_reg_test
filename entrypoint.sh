#!/bin/bash
set -e

# Запустите миграции если файл alembic.ini существует
if [ -f "alembic.ini" ]; then
  echo "Running migrations..."
  uv run alembic upgrade head || echo "Migrations failed, continuing..."
fi

# Запустите приложение через uv из корневой директории
echo "Starting application..."
cd /app
exec uv run python app/main.py