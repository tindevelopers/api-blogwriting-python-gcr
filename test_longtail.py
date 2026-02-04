#!/usr/bin/env python3
"""
Test script to get longtail keywords from /api/v1/keywords/enhanced
"""

import json
import requests

BASE_URL = "https://blog-writer-api-dev-kq42l26tuq-od.a.run.app"

def get_longtail_keywords(keyword: str):
    """Get longtail keywords for a given keyword."""
    url = f"{BASE_URL}/api/v1/keywords/enhanced"
    
    payload = {
        "keywords": [keyword],
        "location": "United States",
        "language": "en",
        "max_suggestions_per_keyword": 150
    }
    
    print(f"Requesting longtail keywords for: '{keyword}'")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}\n")
    
    try:
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract longtail keywords
        if keyword in data.get("enhanced_analysis", {}):
            analysis = data["enhanced_analysis"][keyword]
            longtail_keywords = analysis.get("long_tail_keywords", [])
            
            print("=" * 80)
            print(f"LONGTAIL KEYWORDS FOR: '{keyword}'")
            print("=" * 80)
            print(f"\nTotal longtail keywords found: {len(longtail_keywords)}\n")
            
            if longtail_keywords:
                print("Longtail Keywords List:")
                print("-" * 80)
                for i, kw in enumerate(longtail_keywords, 1):
                    print(f"{i:3d}. {kw}")
            else:
                print("No longtail keywords found in 'long_tail_keywords' field.")
            
            # Also check if we can filter from other sources
            print("\n" + "=" * 80)
            print("ADDITIONAL ANALYSIS")
            print("=" * 80)
            
            # Filter all keywords by word count (3+ words)
            all_keywords = list(data.get("enhanced_analysis", {}).keys())
            filtered_longtail = [kw for kw in all_keywords if kw != keyword and len(kw.split()) >= 3]
            
            if filtered_longtail:
                print(f"\nFound {len(filtered_longtail)} additional longtail keywords (filtered from all keywords):")
                for i, kw in enumerate(filtered_longtail[:20], 1):  # Show first 20
                    print(f"{i:3d}. {kw}")
                if len(filtered_longtail) > 20:
                    print(f"... and {len(filtered_longtail) - 20} more")
            
            # Check suggested_keywords
            suggested_keywords = data.get("suggested_keywords", [])
            if suggested_keywords:
                suggested_longtail = [kw for kw in suggested_keywords if len(kw.split()) >= 3]
                if suggested_longtail:
                    print(f"\nFound {len(suggested_longtail)} longtail keywords in 'suggested_keywords':")
                    for i, kw in enumerate(suggested_longtail[:20], 1):  # Show first 20
                        print(f"{i:3d}. {kw}")
                    if len(suggested_longtail) > 20:
                        print(f"... and {len(suggested_longtail) - 20} more")
            
            # Show related keywords
            related_keywords = analysis.get("related_keywords", [])
            if related_keywords:
                related_longtail = [kw for kw in related_keywords if len(kw.split()) >= 3]
                if related_longtail:
                    print(f"\nFound {len(related_longtail)} longtail keywords in 'related_keywords':")
                    for i, kw in enumerate(related_longtail[:20], 1):
                        print(f"{i:3d}. {kw}")
                    if len(related_longtail) > 20:
                        print(f"... and {len(related_longtail) - 20} more")
            
            # Summary
            print("\n" + "=" * 80)
            print("SUMMARY")
            print("=" * 80)
            print(f"Explicit longtail keywords (long_tail_keywords): {len(longtail_keywords)}")
            print(f"Filtered from all keywords (3+ words): {len(filtered_longtail)}")
            if suggested_keywords:
                print(f"Filtered from suggested_keywords (3+ words): {len([kw for kw in suggested_keywords if len(kw.split()) >= 3])}")
            if related_keywords:
                print(f"Filtered from related_keywords (3+ words): {len(related_longtail)}")
            
            # Combine all unique longtail keywords
            all_longtail = set(longtail_keywords)
            all_longtail.update(filtered_longtail)
            if suggested_keywords:
                all_longtail.update([kw for kw in suggested_keywords if len(kw.split()) >= 3])
            if related_keywords:
                all_longtail.update([kw for kw in related_keywords if len(kw.split()) >= 3])
            
            print(f"\nTotal unique longtail keywords (all sources): {len(all_longtail)}")
            
            return {
                "explicit_longtail": longtail_keywords,
                "filtered_longtail": filtered_longtail,
                "all_unique_longtail": sorted(list(all_longtail)),
                "full_response": data
            }
        else:
            print(f"Keyword '{keyword}' not found in response.")
            print(f"Available keywords: {list(data.get('enhanced_analysis', {}).keys())}")
            return None
            
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        try:
            error_detail = e.response.json()
            print(f"Error details: {json.dumps(error_detail, indent=2)}")
        except:
            print(f"Error response: {e.response.text}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = get_longtail_keywords("dog groomer")
    
    if result:
        print("\n" + "=" * 80)
        print("COMPLETE LONGTAIL KEYWORDS LIST")
        print("=" * 80)
        for i, kw in enumerate(result["all_unique_longtail"], 1):
            print(f"{i:3d}. {kw}")
