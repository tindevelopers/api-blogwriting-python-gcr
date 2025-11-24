#!/bin/bash
# Test DataForSEO AI Search Volume endpoint paths directly

AUTH="ZGV2ZWxvcGVyQHRpbi5pbmZvOjcyNWVjODhlMGFmMGM5MDU="
BASE_URL="https://api.dataforseo.com/v3"
KEYWORD="chatgpt"

echo "=========================================="
echo "Testing AI Search Volume Endpoints"
echo "=========================================="
echo ""

# Test each endpoint path
ENDPOINTS=(
    "ai_optimization/keyword_data/live"
    "ai_optimization/ai_keyword_data/live"
    "ai_optimization/keywords_data/live"
    "keywords_data/ai_optimization/keyword_data/live"
    "keywords_data/ai_optimization/search_volume/live"
    "ai_optimization/search_volume/live"
)

for endpoint in "${ENDPOINTS[@]}"; do
    echo "=========================================="
    echo "Testing: $endpoint"
    echo "=========================================="
    
    curl -s -X POST "$BASE_URL/$endpoint" \
        -H "Authorization: Basic $AUTH" \
        -H "Content-Type: application/json" \
        -d "[{
            \"keywords\": [\"$KEYWORD\"],
            \"location_name\": \"United States\",
            \"language_code\": \"en\"
        }]" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print('Status:', d.get('status_code'), d.get('status_message', ''))
    if d.get('tasks'):
        task = d['tasks'][0]
        status = task.get('status_code')
        msg = task.get('status_message', '')
        print('Task Status:', status, '-', msg)
        if status == 20000:
            print('✅✅✅ SUCCESS! Endpoint works!')
            r = task.get('result', [])
            if r and len(r) > 0:
                print('Result keys:', list(r[0].keys()))
                if 'keyword_data' in r[0]:
                    kd = r[0]['keyword_data']
                    if 'keyword_info' in kd:
                        ki = kd['keyword_info']
                        print('AI Search Volume:', ki.get('ai_search_volume', 'N/A'))
        elif status == 40204:
            print('✅ Path is CORRECT (subscription needed)')
        elif status == 40402:
            print('❌ Invalid Path (40402)')
        elif status == 40400:
            print('❌ Not Found (40400)')
        else:
            print('⚠️  Status:', status)
except Exception as e:
    print('Error:', e)
"
    echo ""
done

echo "=========================================="
echo "Testing Complete"
echo "=========================================="

