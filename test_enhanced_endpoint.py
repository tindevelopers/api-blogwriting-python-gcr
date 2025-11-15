#!/usr/bin/env python3
"""
Test script for the enhanced blog generation endpoint.
"""
import json
import requests
import sys
import time

def test_enhanced_endpoint():
    """Test the enhanced blog generation endpoint with the test JSON file."""
    
    # Read the test JSON file
    with open('test_notary_california.json', 'r') as f:
        payload = json.load(f)
    
    # Service URL
    url = "https://blog-writer-api-dev-613248238610.europe-west1.run.app/api/v1/blog/generate-enhanced"
    
    print("=" * 60)
    print("Testing Enhanced Blog Generation Endpoint")
    print("=" * 60)
    print(f"\nURL: {url}")
    print(f"\nPayload:")
    print(json.dumps(payload, indent=2))
    print("\n" + "=" * 60)
    print("Sending request...")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=120  # 2 minute timeout for enhanced generation
        )
        
        elapsed_time = time.time() - start_time
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Time: {elapsed_time:.2f} seconds")
        print("\n" + "=" * 60)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS!")
            print("\nResponse Summary:")
            print(f"  Title: {result.get('title', 'N/A')[:80]}...")
            print(f"  Content Length: {len(result.get('content', ''))} characters")
            print(f"  SEO Score: {result.get('seo_score', 'N/A')}")
            print(f"  Readability Score: {result.get('readability_score', 'N/A')}")
            print(f"  Quality Score: {result.get('quality_score', 'N/A')}")
            print(f"  Total Tokens: {result.get('total_tokens', 'N/A')}")
            print(f"  Total Cost: ${result.get('total_cost', 0):.4f}")
            print(f"  Generation Time: {result.get('generation_time', 'N/A')} seconds")
            print(f"  Stage Results: {len(result.get('stage_results', []))} stages")
            
            if result.get('warnings'):
                print(f"\n⚠️  Warnings: {len(result['warnings'])}")
                for warning in result['warnings'][:3]:
                    print(f"    - {warning}")
            
            # Save full response to file
            output_file = 'test_enhanced_response.json'
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n📄 Full response saved to: {output_file}")
            
        else:
            print("❌ ERROR!")
            print(f"\nError Response:")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2))
            except:
                print(response.text[:500])
                
    except requests.exceptions.Timeout:
        print(f"\n⏱️  Request timed out after 120 seconds")
        print("The enhanced generation may still be processing...")
    except Exception as e:
        print(f"\n❌ Exception occurred: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_endpoint()

