#!/usr/bin/env python3
"""
Test DataForSEO AI API via the deployed endpoint to see actual response structure.
This will help us understand what the API is actually returning.
"""

import json
import subprocess
import sys

BASE_URL = "https://blog-writer-api-dev-kq42l26tuq-od.a.run.app"

def test_ai_mentions_endpoint():
    """Test the AI mentions endpoint to see raw response."""
    print("="*80)
    print("Testing AI Mentions Endpoint (Direct API Call)")
    print("="*80)
    print()
    
    payload = {
        "target": "chatgpt",
        "target_type": "keyword",
        "location": "United States",
        "language": "en",
        "platform": "chat_gpt",
        "limit": 10
    }
    
    try:
        result = subprocess.run(
            ['curl', '-s', '-X', 'POST',
             f'{BASE_URL}/api/v1/keywords/ai-mentions',
             '-H', 'Content-Type: application/json',
             '-d', json.dumps(payload),
             '--max-time', '60'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            
            print("✅ Response received")
            print()
            print("Full Response Structure:")
            print(json.dumps(data, indent=2, default=str))
            
            # Analyze the structure
            llm_mentions = data.get('llm_mentions', {})
            print()
            print("="*80)
            print("Analysis:")
            print("="*80)
            print(f"AI Search Volume: {llm_mentions.get('ai_search_volume', 0):,}")
            print(f"Mentions Count: {llm_mentions.get('mentions_count', 0):,}")
            print(f"Top Pages: {len(llm_mentions.get('top_pages', []))}")
            print(f"Top Domains: {len(llm_mentions.get('top_domains', []))}")
            print(f"Topics: {len(llm_mentions.get('topics', []))}")
            
            aggregated_metrics = llm_mentions.get('aggregated_metrics', {})
            if aggregated_metrics:
                print()
                print("Aggregated Metrics Keys:", list(aggregated_metrics.keys()))
                print("Aggregated Metrics:", json.dumps(aggregated_metrics, indent=2, default=str))
            
            return data
        else:
            print(f"❌ Error: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return None


def check_recent_logs():
    """Check recent Cloud Run logs for API response details."""
    print()
    print("="*80)
    print("Checking Recent Cloud Run Logs")
    print("="*80)
    print()
    
    try:
        result = subprocess.run(
            ['gcloud', 'logging', 'read',
             'resource.type=cloud_run_revision AND resource.labels.service_name=blog-writer-api-dev',
             '--limit', '20',
             '--format=json',
             '--freshness=5m'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            logs = json.loads(result.stdout)
            print(f"Found {len(logs)} recent log entries")
            print()
            
            # Look for DataForSEO related logs
            dataforseo_logs = []
            for log in logs:
                message = log.get('jsonPayload', {}).get('message', '')
                if 'DataForSEO' in message or 'AI search volume' in message or 'LLM mentions' in message:
                    dataforseo_logs.append(log)
            
            if dataforseo_logs:
                print(f"Found {len(dataforseo_logs)} DataForSEO related logs:")
                print()
                for log in dataforseo_logs[:5]:
                    payload = log.get('jsonPayload', {})
                    message = payload.get('message', '')
                    timestamp = log.get('timestamp', '')
                    print(f"[{timestamp}] {message[:200]}")
                    print()
            else:
                print("No DataForSEO related logs found in recent entries")
        else:
            print(f"⚠️  Could not fetch logs: {result.stderr}")
            
    except Exception as e:
        print(f"⚠️  Could not check logs: {e}")


def main():
    """Run tests."""
    print("\n" + "="*80)
    print("DATAFORSEO AI API TEST - Via Deployed Endpoint")
    print("="*80)
    print()
    
    # Test the endpoint
    result = test_ai_mentions_endpoint()
    
    # Check logs
    check_recent_logs()
    
    print()
    print("="*80)
    print("Summary")
    print("="*80)
    print()
    
    if result:
        llm_mentions = result.get('llm_mentions', {})
        has_data = (
            llm_mentions.get('ai_search_volume', 0) > 0 or
            llm_mentions.get('mentions_count', 0) > 0 or
            len(llm_mentions.get('top_pages', [])) > 0
        )
        
        if has_data:
            print("✅ SUCCESS: API returned data!")
        else:
            print("⚠️  API returned structure but no data (all zeros/empty)")
            print("   This could mean:")
            print("   1. DataForSEO doesn't have data for 'chatgpt'")
            print("   2. API response structure is different than expected")
            print("   3. Need to check Cloud Run logs for actual API response")
    else:
        print("❌ Failed to get response from endpoint")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

