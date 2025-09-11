#!/bin/bash
set -e

# Set default port if not provided
export PORT=${PORT:-8000}

echo "Starting Blog Writer SDK on port $PORT"

# Start the application
exec python -m uvicorn main:app --host 0.0.0.0 --port "$PORT"
