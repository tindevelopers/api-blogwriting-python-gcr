#!/bin/bash
# Monitor Cloud Run Deployment Status
# Continuously checks deployment status and logs until successful

set -e

PROJECT="api-ai-blog-writer"
SERVICE="blog-writer-api-dev"
REGION="europe-west9"
MAX_ATTEMPTS=30
ATTEMPT=0
SLEEP_INTERVAL=10

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Monitoring Cloud Run Deployment: $SERVICE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Function to check build status
check_build_status() {
    echo "📦 Checking Cloud Build status..."
    gcloud builds list --limit=1 --format="table(id,status,createTime)" --project=$PROJECT 2>&1 | head -5
    echo ""
}

# Function to check latest revision
check_revision_status() {
    echo "🔍 Checking latest revision..."
    LATEST_REVISION=$(gcloud run services describe $SERVICE --region=$REGION --format="value(status.latestCreatedRevisionName)" --project=$PROJECT 2>&1)
    READY_REVISION=$(gcloud run services describe $SERVICE --region=$REGION --format="value(status.latestReadyRevisionName)" --project=$PROJECT 2>&1)
    
    echo "Latest Created: $LATEST_REVISION"
    echo "Latest Ready: $READY_REVISION"
    
    if [ "$LATEST_REVISION" == "$READY_REVISION" ] && [ -n "$LATEST_REVISION" ]; then
        echo "✅ Latest revision is ready!"
        return 0
    else
        echo "⏳ Revision not ready yet..."
        return 1
    fi
}

# Function to check for errors in logs
check_logs_for_errors() {
    echo "📋 Checking recent logs for errors..."
    
    # Check for critical errors
    ERRORS=$(gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE AND severity>=ERROR" --limit=5 --format="value(textPayload,jsonPayload.message)" --project=$PROJECT 2>&1 | grep -v "^$" | head -10)
    
    if [ -n "$ERRORS" ]; then
        echo "❌ Errors found:"
        echo "$ERRORS"
        return 1
    else
        echo "✅ No critical errors found"
        return 0
    fi
}

# Function to check for successful startup
check_startup_success() {
    echo "🚀 Checking for successful startup..."
    
    STARTUP_LOG=$(gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE AND textPayload=~'Starting Blog Writer SDK'" --limit=1 --format="value(textPayload)" --project=$PROJECT 2>&1)
    
    if [ -n "$STARTUP_LOG" ]; then
        echo "✅ Service started successfully!"
        echo "   $STARTUP_LOG"
        return 0
    else
        echo "⏳ Waiting for startup message..."
        return 1
    fi
}

# Function to check for syntax errors
check_syntax_errors() {
    echo "🔍 Checking for syntax errors..."
    
    SYNTAX_ERRORS=$(gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE AND (textPayload=~'IndentationError' OR textPayload=~'SyntaxError')" --limit=5 --format="value(textPayload)" --project=$PROJECT 2>&1 | grep -v "^$")
    
    if [ -n "$SYNTAX_ERRORS" ]; then
        echo "❌ Syntax errors found:"
        echo "$SYNTAX_ERRORS"
        return 1
    else
        echo "✅ No syntax errors"
        return 0
    fi
}

# Main monitoring loop
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Attempt $ATTEMPT/$MAX_ATTEMPTS ($(date +'%H:%M:%S'))"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Check build status
    check_build_status
    
    # Check revision status
    if check_revision_status; then
        # Check for syntax errors first
        if check_syntax_errors; then
            # Check for startup success
            if check_startup_success; then
                # Check for other errors
                if check_logs_for_errors; then
                    echo ""
                    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                    echo "✅ DEPLOYMENT SUCCESSFUL!"
                    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                    exit 0
                fi
            fi
        else
            echo ""
            echo "❌ Syntax errors detected - deployment failed"
            echo "   Check logs for details and fix code"
            exit 1
        fi
    fi
    
    if [ $ATTEMPT -lt $MAX_ATTEMPTS ]; then
        echo ""
        echo "⏳ Waiting ${SLEEP_INTERVAL}s before next check..."
        sleep $SLEEP_INTERVAL
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⏱️  Timeout: Maximum attempts reached"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Checking final status..."
check_revision_status
check_logs_for_errors
check_syntax_errors

exit 1

