#!/usr/bin/env python3
"""
Test script to call the API directly for creating topics and subtopics for 100 words.
"""

import json
import requests
from typing import Dict, Any

# API Configuration
BASE_URL = "https://blog-writer-api-dev-kq42l26tuq-od.a.run.app"
ENDPOINT = f"{BASE_URL}/api/v1/blog/generate-enhanced"

def test_api_100_words() -> None:
    """Test the API with a 100-word target."""
    
    print("=" * 60)
    print("Testing API: Generate Blog with 100 Words")
    print("=" * 60)
    print(f"\nEndpoint: {ENDPOINT}\n")
    
    # Test payload with 100 word target
    payload: Dict[str, Any] = {
        "topic": "Introduction to Python Programming",
        "keywords": ["python", "programming", "coding"],
        "blog_type": "tutorial",
        "tone": "professional",
        "length": "short",
        "word_count_target": 100,
        "optimize_for_traffic": True,
        "use_dataforseo_content_generation": True
    }
    
    print("Request Payload:")
    print(json.dumps(payload, indent=2))
    print("\nSending request...\n")
    
    try:
        # Make the API call
        response = requests.post(
            ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120  # 2 minute timeout for content generation
        )
        
        print("=" * 60)
        print(f"Response Status: {response.status_code}")
        print("=" * 60)
        print()
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ SUCCESS - Full Response:")
            print(json.dumps(data, indent=2))
            
            print("\n" + "=" * 60)
            print("Extracted Information:")
            print("=" * 60)
            
            # Extract key fields
            title = data.get("title", "N/A")
            seo_metadata = data.get("seo_metadata", {})
            word_count_range = seo_metadata.get("word_count_range", {})
            actual_word_count = word_count_range.get("actual", "N/A")
            subtopics = seo_metadata.get("subtopics", [])
            subtopics_count = len(subtopics)
            seo_score = data.get("seo_score", "N/A")
            cost = data.get("total_cost", "N/A")
            content = data.get("content", "")
            content_word_count = len(content.split()) if content else 0
            
            print(f"Title: {title}")
            print(f"Content Word Count: {content_word_count}")
            print(f"Target Word Count Range: {word_count_range.get('min', 'N/A')} - {word_count_range.get('max', 'N/A')}")
            print(f"Actual Word Count (from metadata): {actual_word_count}")
            print(f"Subtopics Count: {subtopics_count}")
            print(f"SEO Score: {seo_score}")
            print(f"Total Cost: ${cost}")
            print()
            
            if subtopics_count > 0:
                print("Subtopics:")
                for i, subtopic in enumerate(subtopics, 1):
                    print(f"  {i}. {subtopic}")
            else:
                print("⚠️  No subtopics generated")
            
            print("\n" + "=" * 60)
            print("Content Preview (first 200 chars):")
            print("=" * 60)
            if content:
                print(content[:200] + "..." if len(content) > 200 else content)
            else:
                print("No content returned")
            
        else:
            print(f"❌ ERROR - Status Code: {response.status_code}")
            try:
                error_data = response.json()
                print("Error Response:")
                print(json.dumps(error_data, indent=2))
            except:
                print("Error Response (text):")
                print(response.text)
    
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out (exceeded 120 seconds)")
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to the API")
        print(f"   Check if the endpoint is accessible: {ENDPOINT}")
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {str(e)}")
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    test_api_100_words()










