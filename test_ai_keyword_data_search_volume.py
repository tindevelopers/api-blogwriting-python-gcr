#!/usr/bin/env python3
"""
Test DataForSEO AI Keyword Data Search Volume endpoint based on official documentation.
Endpoint name: ai_optimization_keyword_data_search_volume
"""
import json
import requests
import base64

# API credentials
USERNAME = "developer@tin.info"
PASSWORD = "725ec88e0af0c905"
AUTH_HEADER = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()
BASE_URL = "https://api.dataforseo.com/v3"

# Test keyword
KEYWORD = "chatgpt"

# Based on documentation: endpoint name is "ai_optimization_keyword_data_search_volume"
# This likely translates to: "ai_optimization/keyword_data/search_volume/live"
ENDPOINTS_TO_TEST = [
    "ai_optimization/keyword_data/search_volume/live",  # From doc: ai_optimization_keyword_data_search_volume
    "ai_optimization/keyword_data/live",  # Alternative (without search_volume)
    "ai_optimization/keyword_data_search_volume/live",  # Alternative format
]

def test_endpoint(endpoint_path):
    """Test a specific endpoint path."""
    url = f"{BASE_URL}/{endpoint_path}"
    
    # Based on documentation parameters:
    payload = [{
        "keywords": [KEYWORD],
        "language_code": "en",  # Required
        "location_name": "United States"  # Optional, defaults to United States
    }]
    
    headers = {
        "Authorization": f"Basic {AUTH_HEADER}",
        "Content-Type": "application/json"
    }
    
    print(f"\n{'='*80}")
    print(f"Testing: {endpoint_path}")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"{'='*80}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None
        
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")
            print(f"Response: {response.text[:500]}")
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
                    ai_vol = None
                    keyword = None
                    
                    # Check different possible response structures
                    if "keyword" in first_result:
                        keyword = first_result.get("keyword")
                        print(f"Keyword: {keyword}")
                    
                    if "keyword_data" in first_result:
                        keyword_data = first_result.get("keyword_data", {})
                        keyword_info = keyword_data.get("keyword_info", {})
                        ai_vol = keyword_info.get("ai_search_volume", None)
                        if ai_vol:
                            print(f"✅ AI Search Volume found in keyword_data.keyword_info: {ai_vol}")
                    
                    if not ai_vol and "ai_search_volume" in first_result:
                        ai_vol = first_result.get("ai_search_volume")
                        print(f"✅ AI Search Volume found (direct): {ai_vol}")
                    
                    if not ai_vol:
                        print("⚠️  No AI search volume found in result")
                    
                    # Check for monthly searches
                    monthly_searches = []
                    if "keyword_data" in first_result:
                        keyword_data = first_result.get("keyword_data", {})
                        keyword_info = keyword_data.get("keyword_info", {})
                        monthly_searches = keyword_info.get("monthly_searches", [])
                        if monthly_searches:
                            print(f"✅ Monthly searches found: {len(monthly_searches)} months")
                    
                    print("\nFull result structure:")
                    print(json.dumps(first_result, indent=2, default=str)[:2000])
                return True
            elif task_status == 40204:
                print("✅ Path is CORRECT but subscription/access needed")
                print("   This means the endpoint path is valid!")
                return True  # Path is correct, just needs subscription
            elif task_status == 40402:
                print("❌ Invalid Path (40402)")
                return False
            elif task_status == 40400:
                print("❌ Not Found (40400)")
                return False
            else:
                print(f"⚠️  Unexpected status: {task_status}")
                print(f"   Message: {task_message}")
                return None
        else:
            print("⚠️  No tasks in response")
            print(f"Full response: {json.dumps(data, indent=2, default=str)[:500]}")
            return None
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("="*80)
    print("DataForSEO AI Keyword Data Search Volume Endpoint Test")
    print("Based on official documentation: ai_optimization_keyword_data_search_volume")
    print("="*80)
    print(f"Testing keyword: {KEYWORD}")
    print(f"Testing {len(ENDPOINTS_TO_TEST)} endpoint paths...")
    print(f"Base URL: {BASE_URL}")
    
    successful_paths = []
    failed_paths = []
    unknown_paths = []
    
    for endpoint_path in ENDPOINTS_TO_TEST:
        result = test_endpoint(endpoint_path)
        if result is True:
            successful_paths.append(endpoint_path)
        elif result is False:
            failed_paths.append(endpoint_path)
        else:
            unknown_paths.append(endpoint_path)
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    if successful_paths:
        print(f"\n✅ Successful paths ({len(successful_paths)}):")
        for path in successful_paths:
            print(f"   - {path}")
        print("\n🎉 FOUND WORKING ENDPOINT(S)!")
    else:
        print("\n❌ No successful paths found")
        print("   The code will use LLM mentions endpoint as fallback.")
    
    if failed_paths:
        print(f"\n❌ Failed paths ({len(failed_paths)}):")
        for path in failed_paths:
            print(f"   - {path}")
    
    if unknown_paths:
        print(f"\n⚠️  Unknown status paths ({len(unknown_paths)}):")
        for path in unknown_paths:
            print(f"   - {path}")
    
    print("\n" + "="*80)
    print("Documentation Reference:")
    print("Endpoint name: ai_optimization_keyword_data_search_volume")
    print("Parameters: keywords (required), language_code (required), location_name (optional)")
    print("="*80)

if __name__ == "__main__":
    main()

