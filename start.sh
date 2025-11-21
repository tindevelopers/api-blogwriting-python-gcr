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
        # Plain text format (env file) - load selectively to avoid overriding individual secrets
        # Individual secrets (set via --update-secrets) take precedence
        while IFS= read -r line || [ -n "$line" ]; do
            # Skip comments and empty lines
            [[ "$line" =~ ^[[:space:]]*# ]] && continue
            [[ -z "${line// }" ]] && continue
            [[ ! "$line" =~ = ]] && continue
            
            # Split on first = only
            key="${line%%=*}"
            value="${line#*=}"
            
            # Remove leading/trailing whitespace
            key=$(echo "$key" | xargs)
            value=$(echo "$value" | xargs)
            
            # Skip if key is already set (individual secrets take precedence)
            if [ -z "${!key}" ]; then
                # Skip placeholder values
                if [[ ! "$value" =~ ^(your_|YOUR_|placeholder) ]] && [[ -n "$value" ]]; then
                    export "$key=$value"
                fi
            fi
        done < /secrets/env
        echo "✅ Secrets loaded from /secrets/env (plain text format, placeholders skipped)"
    fi
else
    echo "⚠️  No secrets file found at /secrets/env, using environment variables only"
fi

echo "Starting Blog Writer SDK on port $PORT"

# Start the application
exec python -m uvicorn main:app --host 0.0.0.0 --port "$PORT"




