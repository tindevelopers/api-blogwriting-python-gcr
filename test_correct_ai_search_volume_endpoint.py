#!/usr/bin/env python3
"""
Test the CORRECT DataForSEO AI Search Volume endpoint path.
Correct path: ai_optimization/ai_keyword_data/keywords_search_volume/live
Source: https://docs.dataforseo.com/v3/ai_optimization/ai_keyword_data/keywords_search_volume/live/
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

# CORRECT endpoint path from official documentation
CORRECT_ENDPOINT = "ai_optimization/ai_keyword_data/keywords_search_volume/live"

def test_endpoint():
    """Test the correct endpoint path."""
    url = f"{BASE_URL}/{CORRECT_ENDPOINT}"
    
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
    
    print("="*80)
    print("Testing CORRECT DataForSEO AI Search Volume Endpoint")
    print("="*80)
    print(f"Endpoint: {CORRECT_ENDPOINT}")
    print(f"URL: {url}")
    print(f"Keyword: {KEYWORD}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("="*80)
    
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
        
        print(f"\nResponse Status Code: {status_code}")
        print(f"Response Status Message: {status_message}")
        
        if data.get("tasks") and len(data["tasks"]) > 0:
            task = data["tasks"][0]
            task_status = task.get("status_code")
            task_message = task.get("status_message", "")
            
            print(f"\nTask Status Code: {task_status}")
            print(f"Task Status Message: {task_message}")
            
            if task_status == 20000:
                print("\n✅✅✅ SUCCESS! Endpoint path is CORRECT and returns data!")
                result_data = task.get("result", [])
                if result_data and len(result_data) > 0:
                    print(f"\nResult count: {len(result_data)}")
                    first_result = result_data[0]
                    print(f"Result keys: {list(first_result.keys())}")
                    
                    # Check for AI search volume data
                    ai_vol = None
                    keyword = None
                    
                    # Check different possible response structures
                    if "keyword" in first_result:
                        keyword = first_result.get("keyword")
                        print(f"\nKeyword: {keyword}")
                    
                    if "keyword_data" in first_result:
                        keyword_data = first_result.get("keyword_data", {})
                        keyword_info = keyword_data.get("keyword_info", {})
                        ai_vol = keyword_info.get("ai_search_volume", None)
                        if ai_vol:
                            print(f"✅ AI Search Volume: {ai_vol}")
                    
                    if not ai_vol and "ai_search_volume" in first_result:
                        ai_vol = first_result.get("ai_search_volume")
                        print(f"✅ AI Search Volume (direct): {ai_vol}")
                    
                    # Check for monthly searches
                    monthly_searches = []
                    if "keyword_data" in first_result:
                        keyword_data = first_result.get("keyword_data", {})
                        keyword_info = keyword_data.get("keyword_info", {})
                        monthly_searches = keyword_info.get("monthly_searches", [])
                        if monthly_searches:
                            print(f"✅ Monthly searches: {len(monthly_searches)} months")
                            print(f"   Latest month: {monthly_searches[0] if monthly_searches else 'N/A'}")
                    
                    print("\n" + "="*80)
                    print("Full Result Structure:")
                    print("="*80)
                    print(json.dumps(first_result, indent=2, default=str)[:2000])
                return True
            elif task_status == 40204:
                print("\n✅ Path is CORRECT but subscription/access needed")
                print("   This confirms the endpoint path is valid!")
                return True  # Path is correct, just needs subscription
            elif task_status == 40402:
                print("\n❌ Invalid Path (40402)")
                return False
            elif task_status == 40400:
                print("\n❌ Not Found (40400)")
                return False
            else:
                print(f"\n⚠️  Unexpected status: {task_status}")
                print(f"   Message: {task_message}")
                return None
        else:
            print("\n⚠️  No tasks in response")
            print(f"Full response: {json.dumps(data, indent=2, default=str)[:500]}")
            return None
            
    except requests.exceptions.Timeout:
        print("\n❌ Request timeout")
        return None
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request error: {e}")
        return None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = test_endpoint()
    
    print("\n" + "="*80)
    if result is True:
        print("✅ TEST PASSED - Endpoint path is CORRECT!")
    elif result is False:
        print("❌ TEST FAILED - Endpoint path is incorrect")
    else:
        print("⚠️  TEST INCONCLUSIVE - Check response above")
    print("="*80)
    print("\nDocumentation: https://docs.dataforseo.com/v3/ai_optimization/ai_keyword_data/keywords_search_volume/live/")

