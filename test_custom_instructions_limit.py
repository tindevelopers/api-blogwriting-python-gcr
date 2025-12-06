#!/usr/bin/env python3
"""
Test script for custom_instructions limit increase to 5000 characters.
Tests various scenarios to verify the limit works correctly.
"""

import requests
import json
import time
from typing import Dict, Any

# Local API endpoint
BASE_URL = "http://localhost:8000"

def test_custom_instructions_length(length: int, description: str) -> Dict[str, Any]:
    """Test custom_instructions with a specific length."""
    print(f"\n{'='*60}")
    print(f"Test: {description}")
    print(f"Length: {length} characters")
    print(f"{'='*60}")
    
    # Generate custom_instructions of specified length
    if length <= 0:
        custom_instructions = None
    else:
        # Create a meaningful instruction that's exactly the specified length
        base_instruction = "MANDATORY STRUCTURE: Use H1 for title, H2 for sections, include internal links, add images with alt text. "
        repeat_count = (length - len(base_instruction)) // len("Repeat this instruction. ")
        custom_instructions = base_instruction + ("Repeat this instruction. " * repeat_count)
        custom_instructions = custom_instructions[:length]  # Trim to exact length
    
    payload = {
        "topic": "Test Blog Post",
        "keywords": ["test", "blogging"],
        "tone": "professional",
        "length": "short",
        "custom_instructions": custom_instructions
    }
    
    if custom_instructions:
        actual_length = len(custom_instructions)
        print(f"Actual custom_instructions length: {actual_length} characters")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/v1/blog/generate-enhanced",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        elapsed_time = time.time() - start_time
        
        result = {
            "test": description,
            "requested_length": length,
            "actual_length": len(custom_instructions) if custom_instructions else 0,
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "elapsed_time": round(elapsed_time, 2),
            "error": None
        }
        
        if response.status_code == 200:
            data = response.json()
            result["has_content"] = "content" in data or "title" in data
            result["response_keys"] = list(data.keys())[:5]  # First 5 keys
            print(f"✅ SUCCESS - Status: {response.status_code}")
            print(f"   Response time: {elapsed_time:.2f}s")
            print(f"   Response keys: {result['response_keys']}")
        else:
            try:
                error_data = response.json()
                result["error"] = error_data.get("detail", str(error_data))
                print(f"❌ FAILED - Status: {response.status_code}")
                print(f"   Error: {result['error']}")
            except:
                result["error"] = response.text[:200]
                print(f"❌ FAILED - Status: {response.status_code}")
                print(f"   Error: {result['error']}")
        
        return result
        
    except requests.exceptions.ConnectionError:
        print(f"❌ CONNECTION ERROR - Is the server running at {BASE_URL}?")
        return {
            "test": description,
            "requested_length": length,
            "status_code": None,
            "success": False,
            "error": "Connection refused - server not running"
        }
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return {
            "test": description,
            "requested_length": length,
            "status_code": None,
            "success": False,
            "error": str(e)
        }

def main():
    """Run all tests."""
    print("🧪 Testing Custom Instructions Limit Increase")
    print(f"Testing endpoint: {BASE_URL}/api/v1/blog/generate-enhanced")
    print(f"Expected limit: 5000 characters")
    
    results = []
    
    # Test 1: No custom_instructions (None)
    results.append(test_custom_instructions_length(0, "No custom_instructions"))
    
    # Test 2: Small instruction (under old limit)
    results.append(test_custom_instructions_length(500, "Small instruction (500 chars)"))
    
    # Test 3: Medium instruction (under old limit)
    results.append(test_custom_instructions_length(1500, "Medium instruction (1500 chars)"))
    
    # Test 4: At old enhanced limit
    results.append(test_custom_instructions_length(2000, "At old enhanced limit (2000 chars)"))
    
    # Test 5: Between old and new limit
    results.append(test_custom_instructions_length(3500, "Between old and new limit (3500 chars)"))
    
    # Test 6: At new limit
    results.append(test_custom_instructions_length(5000, "At new limit (5000 chars)"))
    
    # Test 7: Over new limit (should fail)
    results.append(test_custom_instructions_length(5001, "Over new limit (5001 chars - should fail)"))
    
    # Test 8: Way over limit (should fail)
    results.append(test_custom_instructions_length(10000, "Way over limit (10000 chars - should fail)"))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for r in results if r.get("success"))
    failed = sum(1 for r in results if not r.get("success"))
    
    print(f"Total tests: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    # Detailed results
    print(f"\n{'='*60}")
    print("DETAILED RESULTS")
    print(f"{'='*60}")
    
    for result in results:
        status = "✅ PASS" if result.get("success") else "❌ FAIL"
        print(f"{status} - {result['test']}")
        print(f"   Length: {result.get('actual_length', 0)} chars")
        if result.get("status_code"):
            print(f"   Status: {result['status_code']}")
        if result.get("error"):
            print(f"   Error: {result['error'][:100]}")
        if result.get("elapsed_time"):
            print(f"   Time: {result['elapsed_time']}s")
    
    return results

if __name__ == "__main__":
    results = main()
    
    # Save results to JSON for later processing
    with open("test_custom_instructions_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n✅ Results saved to test_custom_instructions_results.json")

