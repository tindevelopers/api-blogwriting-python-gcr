#!/bin/bash
# Poll async jobs for Euras Technology test

API_URL="${API_URL:-https://blog-writer-api-dev-kq42l26tuq-od.a.run.app}"

QUICK_JOB_ID="e79d6c53-5e90-45b5-8372-c87df4278cd0"
MULTI_JOB_ID="e9aa8599-686e-4415-bc06-4b2c5a1291a0"

echo "Polling Quick Generate job: ${QUICK_JOB_ID}"
echo "Polling Multi-Phase job: ${MULTI_JOB_ID}"
echo ""

for i in {1..30}; do
    echo "Attempt $i..."
    
    # Check Quick Generate
    QUICK_STATUS=$(curl -s "${API_URL}/api/v1/blog/jobs/${QUICK_JOB_ID}" | jq -r '.status' 2>/dev/null)
    echo "Quick Generate: ${QUICK_STATUS}"
    
    # Check Multi-Phase
    MULTI_STATUS=$(curl -s "${API_URL}/api/v1/blog/jobs/${MULTI_JOB_ID}" | jq -r '.status' 2>/dev/null)
    echo "Multi-Phase: ${MULTI_STATUS}"
    
    if [ "$QUICK_STATUS" = "completed" ] && [ "$MULTI_STATUS" = "completed" ]; then
        echo "Both jobs completed!"
        break
    fi
    
    sleep 5
done

# Get final results
echo ""
echo "=== Quick Generate Result ==="
curl -s "${API_URL}/api/v1/blog/jobs/${QUICK_JOB_ID}" | jq '.' > test_euras_quick_final.json
cat test_euras_quick_final.json | jq -r '.content' 2>/dev/null | head -20

echo ""
echo "=== Multi-Phase Result ==="
curl -s "${API_URL}/api/v1/blog/jobs/${MULTI_JOB_ID}" | jq '.' > test_euras_multi_phase_final.json
cat test_euras_multi_phase_final.json | jq -r '.content' 2>/dev/null | head -20

