#!/bin/bash
# Final check for Euras Technology test jobs

API_URL="https://blog-writer-api-dev-kq42l26tuq-od.a.run.app"

echo "Checking all Euras Technology test jobs..."
echo ""

# Check Quick Generate jobs
for JOB_ID in "5fa33f8d-a14d-4c2c-ad16-57973117a32e" "624548ff-ae00-46b2-a45d-6607d7b819e1"; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Job ID: ${JOB_ID}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    RESPONSE=$(curl -s "${API_URL}/api/v1/blog/jobs/${JOB_ID}")
    STATUS=$(echo "$RESPONSE" | jq -r '.status' 2>/dev/null)
    TITLE=$(echo "$RESPONSE" | jq -r '.title // .result.title' 2>/dev/null)
    CONTENT=$(echo "$RESPONSE" | jq -r '.result.content // .content' 2>/dev/null)
    ERROR=$(echo "$RESPONSE" | jq -r '.error_message // .error' 2>/dev/null)
    
    echo "Status: ${STATUS}"
    echo "Title: ${TITLE}"
    
    if [ -n "$ERROR" ] && [ "$ERROR" != "null" ]; then
        echo "Error: ${ERROR}"
    fi
    
    if [ -n "$CONTENT" ] && [ "$CONTENT" != "null" ]; then
        WORD_COUNT=$(echo "$CONTENT" | wc -w | tr -d ' ')
        echo "Word Count: ${WORD_COUNT}"
        echo ""
        echo "Content Preview (first 500 chars):"
        echo "$CONTENT" | head -c 500
        echo ""
        echo ""
        
        # Save full content
        echo "$RESPONSE" | jq '.' > "test_euras_job_${JOB_ID}.json"
    fi
    
    echo ""
done

