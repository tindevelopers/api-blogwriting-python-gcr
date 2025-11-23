#!/bin/bash
# Test DataForSEO AI Search Volume endpoint to check subscription status

AUTH="ZGV2ZWxvcGVyQHRpbi5pbmZvOjcyNWVjODhlMGFmMGM5MDU="
BASE_URL="https://api.dataforseo.com/v3"
ENDPOINT="ai_optimization/ai_keyword_data/keywords_search_volume/live"

echo "=========================================="
echo "Testing AI Search Volume Endpoint"
echo "=========================================="
echo "Endpoint: $ENDPOINT"
echo "URL: $BASE_URL/$ENDPOINT"
echo ""

curl -s -X POST "$BASE_URL/$ENDPOINT" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d '[{
    "keywords": ["chatgpt"],
    "language_code": "en",
    "location_name": "United States"
  }]' | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print('Response Status:', d.get('status_code'), d.get('status_message', ''))
    if d.get('tasks'):
        task = d['tasks'][0]
        status = task.get('status_code')
        msg = task.get('status_message', '')
        print('Task Status:', status, '-', msg)
        print('')
        if status == 20000:
            print('✅✅✅ SUCCESS! Endpoint works!')
            print('✅ Subscription: ACTIVE')
            r = task.get('result', [])
            if r and len(r) > 0:
                print('Result count:', len(r))
                if 'keyword_data' in r[0]:
                    kd = r[0]['keyword_data']
                    if 'keyword_info' in kd:
                        ki = kd['keyword_info']
                        print('AI Search Volume:', ki.get('ai_search_volume', 'N/A'))
                        ms = ki.get('monthly_searches', [])
                        if ms:
                            print('Monthly Searches:', len(ms), 'months')
        elif status == 40204:
            print('✅ Path is CORRECT!')
            print('❌ Subscription: NOT ACTIVE')
            print('')
            print('Action Required:')
            print('  - Visit DataForSEO Plans and Subscriptions')
            print('  - Activate AI Optimization subscription')
        elif status == 40402:
            print('❌ Invalid Path (40402)')
        elif status == 40400:
            print('❌ Not Found (40400)')
        else:
            print('⚠️  Status:', status)
    else:
        print('No tasks in response')
except Exception as e:
    print('Error:', e)
    import traceback
    traceback.print_exc()
"

