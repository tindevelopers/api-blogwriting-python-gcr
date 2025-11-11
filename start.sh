#!/bin/bash
set -e

# Set default port if not provided
export PORT=${PORT:-8000}

# Load secrets from mounted secret file (if available)
# Cloud Run mounts secrets at /secrets/env (can be JSON or plain text env format)
if [ -f /secrets/env ]; then
    echo "Loading secrets from /secrets/env..."
    # Check if it's JSON format
    if cat /secrets/env | jq . >/dev/null 2>&1; then
        # JSON format - parse with jq
        while IFS="=" read -r key value; do
            # Remove quotes and escape special characters
            key=$(echo "$key" | tr -d '"' | tr -d ' ')
            value=$(echo "$value" | sed 's/^"//;s/"$//')
            # Export as environment variable
            export "$key=$value"
        done < <(cat /secrets/env | jq -r 'to_entries[] | "\(.key)=\(.value)"')
        echo "✅ Secrets loaded from /secrets/env (JSON format)"
    else
        # Plain text format (env file) - source it directly
        set -a  # Automatically export all variables
        source /secrets/env
        set +a
        echo "✅ Secrets loaded from /secrets/env (plain text format)"
    fi
else
    echo "⚠️  No secrets file found at /secrets/env, using environment variables only"
fi

echo "Starting Blog Writer SDK on port $PORT"

# Start the application
exec python -m uvicorn main:app --host 0.0.0.0 --port "$PORT"




