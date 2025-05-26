#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

echo "Migrations complete."

# Execute the command passed as arguments to this script (e.g., uvicorn)
echo "Starting application..."
exec "$@"

