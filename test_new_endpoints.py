#!/usr/bin/env python3
"""
Test script for the 7 recently added endpoints.
Can test individually or all at once.
"""

import json
import requests
import sys
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://blog-writer-api-dev-kq42l26tuq-od.a.run.app"  # Change to your environment
# BASE_URL = "http://localhost:8080"  # For local testing

# Test payloads for each endpoint
PAYLOADS = {
    "goal-based-analysis": {
        "keywords": ["python programming", "web development"],
        "content_goal": "SEO & Rankings",  # Options: "SEO & Rankings", "Engagement", "Conversions", "Brand Awareness"
        "location": "United States",
        "language": "en",
        "include_content_analysis": True,
        "include_serp": True,
        "include_llm_mentions": True
    },
    
    "goal-based-analysis-stream": {
        "keywords": ["python programming"],
        "content_goal": "SEO & Rankings",
        "location": "United States",
        "language": "en",
        "include_content_analysis": True,
        "include_serp": True,
        "include_llm_mentions": True
    },
    
    "ai-optimization": {
        "keywords": ["python tutorial", "learn python", "python programming"],
        "location": "United States",
        "language": "en"
    },
    
    "ai-mentions": {
        "target": "python programming",
        "target_type": "keyword",  # Options: "keyword" or "domain"
        "location": "United States",
        "language": "en",
        "platform": "chat_gpt",  # Options: "chat_gpt" or "google"
        "limit": 100
    },
    
    "ai-topic-suggestions": {
        "keywords": ["python", "web development"],
        "content_objective": "I want to write articles about Python programming and web development",
        "target_audience": "beginner to intermediate developers",
        "industry": "software development",
        "content_goals": ["SEO & Rankings", "Engagement"],
        "location": "United States",
        "language": "en",
        "include_ai_search_volume": True,
        "include_llm_mentions": True,
        "include_llm_responses": False,
        "limit": 50
    },
    
    "ai-topic-suggestions-stream": {
        "keywords": ["python"],
        "content_objective": "Write articles about Python programming",
        "location": "United States",
        "language": "en",
        "include_ai_search_volume": True,
        "include_llm_mentions": True,
        "limit": 20
    },
    
    "topics-recommend": {
        "seed_keywords": ["python", "web development", "programming"],
        "location": "United States",
        "language": "en",
        "max_topics": 20,
        "min_search_volume": 100,
        "max_difficulty": 70.0,
        "include_ai_suggestions": True
    }
}

# Endpoint URLs
ENDPOINTS = {
    "goal-based-analysis": f"{BASE_URL}/api/v1/keywords/goal-based-analysis",
    "goal-based-analysis-stream": f"{BASE_URL}/api/v1/keywords/goal-based-analysis/stream",
    "ai-optimization": f"{BASE_URL}/api/v1/keywords/ai-optimization",
    "ai-mentions": f"{BASE_URL}/api/v1/keywords/ai-mentions",
    "ai-topic-suggestions": f"{BASE_URL}/api/v1/keywords/ai-topic-suggestions",
    "ai-topic-suggestions-stream": f"{BASE_URL}/api/v1/keywords/ai-topic-suggestions/stream",
    "topics-recommend": f"{BASE_URL}/api/v1/topics/recommend"
}


def test_endpoint(name: str, url: str, payload: Dict[str, Any], is_stream: bool = False) -> Dict[str, Any]:
    """Test a single endpoint."""
    print(f"\n{'='*80}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print(f"{'='*80}")
    print(f"Payload:\n{json.dumps(payload, indent=2)}")
    print(f"\nSending request...")
    
    try:
        if is_stream:
            # Handle streaming endpoints
            response = requests.post(url, json=payload, stream=True, timeout=300)
            response.raise_for_status()
            
            print("\nStreaming response:")
            print("-" * 80)
            full_data = []
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # Remove 'data: ' prefix
                        try:
                            data = json.loads(data_str)
                            print(f"Stage: {data.get('stage', 'unknown')} - {data.get('message', '')}")
                            if 'progress' in data:
                                print(f"  Progress: {data['progress']}%")
                            full_data.append(data)
                        except json.JSONDecodeError:
                            print(f"Raw: {line_str}")
            
            return {
                "success": True,
                "status_code": response.status_code,
                "data": full_data,
                "is_stream": True
            }
        else:
            # Handle regular endpoints
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            
            result = response.json()
            print(f"\n✅ Success! Status: {response.status_code}")
            print(f"\nResponse preview (first 500 chars):")
            print("-" * 80)
            result_str = json.dumps(result, indent=2)
            print(result_str[:500] + ("..." if len(result_str) > 500 else ""))
            
            return {
                "success": True,
                "status_code": response.status_code,
                "data": result,
                "is_stream": False
            }
            
    except requests.exceptions.Timeout:
        print(f"\n❌ Timeout: Request took longer than 5 minutes")
        return {"success": False, "error": "Timeout"}
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP Error: {e}")
        try:
            error_detail = e.response.json()
            print(f"Error details: {json.dumps(error_detail, indent=2)}")
        except:
            print(f"Error response: {e.response.text}")
        return {"success": False, "error": str(e), "status_code": e.response.status_code}
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def test_all_endpoints():
    """Test all endpoints sequentially."""
    results = {}
    
    for name, url in ENDPOINTS.items():
        payload = PAYLOADS[name]
        is_stream = "stream" in name
        result = test_endpoint(name, url, payload, is_stream=is_stream)
        results[name] = result
        
        # Small delay between requests
        import time
        time.sleep(1)
    
    # Print summary
    print(f"\n\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    for name, result in results.items():
        status = "✅ PASS" if result.get("success") else "❌ FAIL"
        print(f"{status} - {name}")
        if not result.get("success"):
            print(f"   Error: {result.get('error', 'Unknown error')}")
    
    return results


def test_single_endpoint(endpoint_name: str):
    """Test a single endpoint by name."""
    if endpoint_name not in ENDPOINTS:
        print(f"❌ Unknown endpoint: {endpoint_name}")
        print(f"Available endpoints: {', '.join(ENDPOINTS.keys())}")
        return None
    
    url = ENDPOINTS[endpoint_name]
    payload = PAYLOADS[endpoint_name]
    is_stream = "stream" in endpoint_name
    
    return test_endpoint(endpoint_name, url, payload, is_stream=is_stream)


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Test specific endpoint
        endpoint_name = sys.argv[1]
        test_single_endpoint(endpoint_name)
    else:
        # Test all endpoints
        print("Testing all 7 new endpoints...")
        print(f"Base URL: {BASE_URL}\n")
        test_all_endpoints()


if __name__ == "__main__":
    main()
