#!/usr/bin/env python3
"""
Test different DataForSEO AI Search Volume endpoint paths to find the correct one.
"""
import json
import subprocess
import sys

# API credentials
AUTH = "ZGV2ZWxvcGVyQHRpbi5pbmZvOjcyNWVjODhlMGFmMGM5MDU="
BASE_URL = "https://api.dataforseo.com/v3"

# Test keyword
KEYWORD = "chatgpt"

# Endpoint paths to test
ENDPOINTS_TO_TEST = [
    "ai_optimization/keyword_data/live",
    "ai_optimization/ai_keyword_data/live",
    "ai_optimization/keywords_data/live",
    "keywords_data/ai_optimization/keyword_data/live",
    "keywords_data/ai_optimization/search_volume/live",  # Original (known wrong)
    "ai_optimization/search_volume/live",
]

def test_endpoint(endpoint_path):
    """Test a specific endpoint path."""
    url = f"{BASE_URL}/{endpoint_path}"
    
    payload = [{
        "keywords": [KEYWORD],
        "location_name": "United States",
        "language_code": "en"
    }]
    
    print(f"\n{'='*80}")
    print(f"Testing: {endpoint_path}")
    print(f"{'='*80}")
    
    try:
        result = subprocess.run(
            [
                "curl", "-s", "-X", "POST", url,
                "-H", f"Authorization: Basic {AUTH}",
                "-H", "Content-Type: application/json",
                "-d", json.dumps(payload)
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"❌ curl error: {result.stderr}")
            return None
        
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")
            print(f"Response: {result.stdout[:500]}")
            return None
        
        # Check response
        status_code = data.get("status_code")
        status_message = data.get("status_message", "")
        
        print(f"Status Code: {status_code}")
        print(f"Status Message: {status_message}")
        
        if data.get("tasks") and len(data["tasks"]) > 0:
            task = data["tasks"][0]
            task_status = task.get("status_code")
            task_message = task.get("status_message", "")
            
            print(f"Task Status: {task_status}")
            print(f"Task Message: {task_message}")
            
            if task_status == 20000:
                print("✅✅✅ SUCCESS! Endpoint path is CORRECT!")
                result_data = task.get("result", [])
                if result_data and len(result_data) > 0:
                    print(f"Result count: {len(result_data)}")
                    first_result = result_data[0]
                    print(f"Result keys: {list(first_result.keys())}")
                    
                    # Check for AI search volume data
                    if "keyword_data" in first_result:
                        keyword_data = first_result.get("keyword_data", {})
                        keyword_info = keyword_data.get("keyword_info", {})
                        ai_vol = keyword_info.get("ai_search_volume", 0)
                        print(f"✅ AI Search Volume found: {ai_vol}")
                    
                    if "ai_search_volume" in first_result:
                        print(f"✅ AI Search Volume (direct): {first_result.get('ai_search_volume')}")
                    
                    print("\nSample result:")
                    print(json.dumps(first_result, indent=2, default=str)[:1000])
                return True
            elif task_status == 40204:
                print("✅ Path is CORRECT but subscription/access needed")
                return True  # Path is correct, just needs subscription
            elif task_status == 40402:
                print("❌ Invalid Path (40402)")
                return False
            elif task_status == 40400:
                print("❌ Not Found (40400)")
                return False
            else:
                print(f"⚠️  Unexpected status: {task_status}")
                return None
        else:
            print("⚠️  No tasks in response")
            return None
            
    except subprocess.TimeoutExpired:
        print("❌ Request timeout")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("="*80)
    print("DataForSEO AI Search Volume Endpoint Path Finder")
    print("="*80)
    print(f"Testing keyword: {KEYWORD}")
    print(f"Testing {len(ENDPOINTS_TO_TEST)} endpoint paths...")
    
    successful_paths = []
    failed_paths = []
    
    for endpoint_path in ENDPOINTS_TO_TEST:
        result = test_endpoint(endpoint_path)
        if result is True:
            successful_paths.append(endpoint_path)
        elif result is False:
            failed_paths.append(endpoint_path)
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    if successful_paths:
        print(f"\n✅ Successful paths ({len(successful_paths)}):")
        for path in successful_paths:
            print(f"   - {path}")
    else:
        print("\n❌ No successful paths found")
    
    if failed_paths:
        print(f"\n❌ Failed paths ({len(failed_paths)}):")
        for path in failed_paths:
            print(f"   - {path}")
    
    print("\n" + "="*80)
    print("NOTE: If LLM Mentions endpoint already returns ai_search_volume,")
    print("      we might not need a separate AI Search Volume endpoint.")
    print("="*80)

if __name__ == "__main__":
    main()

