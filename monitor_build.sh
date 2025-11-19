#!/bin/bash
# Monitor Google Cloud Build for new builds

echo "🔍 Monitoring Cloud Build for new builds..."
echo "Commit: $(git log -1 --format='%H %s')"
echo "Branch: $(git branch --show-current)"
echo ""
echo "Press Ctrl+C to stop monitoring"
echo ""

PREVIOUS_BUILD_ID=""
CHECK_COUNT=0

while true; do
    CHECK_COUNT=$((CHECK_COUNT + 1))
    CURRENT_TIME=$(date +"%H:%M:%S")
    
    # Get the latest build
    LATEST_BUILD=$(gcloud builds list --limit=1 --format="value(id,status,createTime)" --sort-by=~createTime 2>/dev/null)
    
    if [ -n "$LATEST_BUILD" ]; then
        BUILD_ID=$(echo "$LATEST_BUILD" | cut -d' ' -f1)
        BUILD_STATUS=$(echo "$LATEST_BUILD" | cut -d' ' -f2)
        BUILD_TIME=$(echo "$LATEST_BUILD" | cut -d' ' -f3-)
        
        # Check if this is a new build
        if [ "$BUILD_ID" != "$PREVIOUS_BUILD_ID" ]; then
            echo "[$CURRENT_TIME] 🆕 NEW BUILD DETECTED!"
            echo "  Build ID: $BUILD_ID"
            echo "  Status: $BUILD_STATUS"
            echo "  Time: $BUILD_TIME"
            echo ""
            
            # Get build details
            BUILD_DETAILS=$(gcloud builds describe "$BUILD_ID" --format="value(source.repoSource.branchName,source.repoSource.commitSha)" 2>/dev/null)
            if [ -n "$BUILD_DETAILS" ]; then
                BRANCH=$(echo "$BUILD_DETAILS" | cut -d' ' -f1)
                COMMIT=$(echo "$BUILD_DETAILS" | cut -d' ' -f2)
                echo "  Branch: $BRANCH"
                echo "  Commit: $COMMIT"
                
                # Check if this matches our commit
                OUR_COMMIT=$(git log -1 --format="%H")
                if [ "$COMMIT" = "$OUR_COMMIT" ]; then
                    echo "  ✅ This build matches our commit!"
                fi
            fi
            
            # Get build log URL
            LOG_URL=$(gcloud builds describe "$BUILD_ID" --format="value(logUrl)" 2>/dev/null)
            if [ -n "$LOG_URL" ]; then
                echo "  Log URL: $LOG_URL"
            fi
            
            echo ""
            PREVIOUS_BUILD_ID="$BUILD_ID"
            
            # If build is complete, show final status
            if [ "$BUILD_STATUS" = "SUCCESS" ] || [ "$BUILD_STATUS" = "FAILURE" ]; then
                echo "🏁 Build completed with status: $BUILD_STATUS"
                break
            fi
        else
            # Same build, check if status changed
            if [ "$BUILD_STATUS" = "SUCCESS" ] || [ "$BUILD_STATUS" = "FAILURE" ]; then
                echo "[$CURRENT_TIME] ✅ Build $BUILD_STATUS"
                break
            elif [ "$BUILD_STATUS" = "WORKING" ] || [ "$BUILD_STATUS" = "QUEUED" ]; then
                echo "[$CURRENT_TIME] ⏳ Build $BUILD_STATUS... (check #$CHECK_COUNT)"
            fi
        fi
    else
        echo "[$CURRENT_TIME] ⏳ No builds found yet... (check #$CHECK_COUNT)"
    fi
    
    sleep 15
done

echo ""
echo "📊 Final Build Status:"
gcloud builds describe "$BUILD_ID" --format="table(id,status,createTime,finishTime,logUrl)" 2>/dev/null

