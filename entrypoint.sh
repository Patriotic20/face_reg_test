#!/bin/bash
set -e

# Run migrations if alembic.ini exists
if [ -f "alembic.ini" ]; then
  echo "Running migrations..."
  uv run alembic upgrade head
fi

# Start application with visible errors
echo "Starting application..."
cd /app
exec python app/main.py