#!/usr/bin/env python3
"""
Test custom_instructions limit on Google Cloud Run with exact character counts.
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "https://blog-writer-api-dev-kq42l26tuq-od.a.run.app"
ENDPOINT = f"{BASE_URL}/api/v1/blog/generate-enhanced"

def generate_text(length: int) -> str:
    """Generate text of exact length."""
    base = "MANDATORY STRUCTURE: Use H1 for title, H2 for sections, include internal links, add images with alt text. "
    repeat = "Repeat this instruction. "
    
    if length <= len(base):
        return base[:length]
    
    remaining = length - len(base)
    repeat_count = remaining // len(repeat)
    text = base + (repeat * repeat_count)
    return text[:length]

def test_length(length: int, description: str, should_pass: bool) -> dict:
    """Test a specific length."""
    print(f"\n{'='*70}")
    print(f"Test: {description}")
    print(f"Requested length: {length} characters")
    print(f"{'='*70}")
    
    # Generate custom_instructions
    if length == 0:
        custom_instructions = None
        payload = {
            "topic": "Test Blog Post - Custom Instructions Limit",
            "keywords": ["test", "blogging", "validation"],
            "tone": "professional",
            "length": "short",
            "blog_type": "guide"
        }
    else:
        custom_instructions = generate_text(length)
        payload = {
            "topic": "Test Blog Post - Custom Instructions Limit",
            "keywords": ["test", "blogging", "validation"],
            "tone": "professional",
            "length": "short",
            "blog_type": "guide",
            "custom_instructions": custom_instructions
        }
    
    actual_length = len(custom_instructions) if custom_instructions else 0
    print(f"Actual custom_instructions length: {actual_length} characters")
    
    if actual_length != length and length > 0:
        print(f"⚠️  WARNING: Length mismatch! Requested {length}, got {actual_length}")
    
    try:
        start_time = time.time()
        response = requests.post(
            ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        elapsed_time = time.time() - start_time
        
        result = {
            "test": description,
            "requested_length": length,
            "actual_length": actual_length,
            "status_code": response.status_code,
            "elapsed_time": round(elapsed_time, 2),
            "success": response.status_code == 200,
            "error": None,
            "response_preview": None
        }
        
        if response.status_code == 200:
            try:
                data = response.json()
                result["response_preview"] = str(list(data.keys())[:5])
                has_content = any(key in data for key in ["content", "title", "blog_content", "blog"])
                print(f"✅ SUCCESS - Status: {response.status_code}")
                print(f"   Response time: {elapsed_time:.2f}s")
                print(f"   Response keys: {result['response_preview']}")
                if has_content:
                    print(f"   ✅ Response contains blog content")
                else:
                    print(f"   ⚠️  Response structure unexpected")
            except:
                result["response_preview"] = response.text[:200]
                print(f"✅ SUCCESS - Status: {response.status_code}")
                print(f"   Response time: {elapsed_time:.2f}s")
        elif response.status_code in [422, 400]:
            try:
                error_data = response.json()
                detail = error_data.get("detail", str(error_data))
                if isinstance(detail, list) and len(detail) > 0:
                    error_msg = detail[0].get("msg", str(detail[0]))
                else:
                    error_msg = str(detail)
                result["error"] = error_msg
                print(f"❌ VALIDATION ERROR - Status: {response.status_code}")
                print(f"   Error: {error_msg}")
                if should_pass:
                    result["success"] = False
                else:
                    result["success"] = True  # Expected failure
                    print(f"   ✅ Correctly rejected (as expected)")
            except:
                result["error"] = response.text[:200]
                print(f"❌ VALIDATION ERROR - Status: {response.status_code}")
                print(f"   Error: {result['error']}")
        else:
            result["error"] = response.text[:200]
            print(f"❌ FAILED - Status: {response.status_code}")
            print(f"   Error: {result['error']}")
        
        return result
        
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return {
            "test": description,
            "requested_length": length,
            "actual_length": actual_length,
            "status_code": None,
            "success": False,
            "error": str(e)
        }

def main():
    """Run all tests."""
    print("🧪 Testing Custom Instructions Limit on Google Cloud Run")
    print("="*70)
    print(f"Endpoint: {ENDPOINT}")
    print(f"Expected limit: 5000 characters")
    print(f"Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    results = []
    
    # Test cases
    test_cases = [
        (0, "No custom_instructions", True),
        (500, "Small instruction (500 chars)", True),
        (2000, "At old enhanced limit (2000 chars)", True),
        (3500, "Between old and new limit (3500 chars)", True),
        (5000, "At new limit (5000 chars)", True),
        (5001, "Over new limit (5001 chars - should fail)", False),
        (6000, "Way over limit (6000 chars - should fail)", False),
    ]
    
    for length, description, should_pass in test_cases:
        result = test_length(length, description, should_pass)
        results.append(result)
    
    # Summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}\n")
    
    passed = sum(1 for r in results if r.get("success"))
    failed = sum(1 for r in results if not r.get("success"))
    
    print(f"Total tests: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}\n")
    
    print("Detailed Results:")
    print("-"*70)
    for result in results:
        status_icon = "✅" if result.get("success") else "❌"
        print(f"{status_icon} {result['test']}")
        print(f"   Length: {result.get('actual_length', 0)} chars")
        print(f"   Status: {result.get('status_code', 'N/A')}")
        if result.get("error"):
            print(f"   Error: {result['error'][:100]}")
        if result.get("elapsed_time"):
            print(f"   Time: {result['elapsed_time']}s")
        print()
    
    # Validation check
    print(f"{'='*70}")
    print("VALIDATION CHECK")
    print(f"{'='*70}\n")
    
    all_correct = True
    for i, (length, description, should_pass) in enumerate(test_cases):
        result = results[i]
        if should_pass:
            if result.get("status_code") == 200:
                print(f"✅ {description}: Correctly accepted")
            else:
                print(f"❌ {description}: INCORRECTLY rejected (Status: {result.get('status_code')})")
                all_correct = False
        else:
            if result.get("status_code") in [422, 400]:
                print(f"✅ {description}: Correctly rejected")
            else:
                print(f"❌ {description}: INCORRECTLY accepted (Status: {result.get('status_code')})")
                all_correct = False
    
    print()
    if all_correct:
        print("🎉 ALL TESTS PASSED - Validation is working correctly!")
    else:
        print("⚠️  SOME TESTS FAILED - Check validation logic")
    
    # Save results
    with open("test_custom_instructions_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "endpoint": ENDPOINT,
            "expected_limit": 5000,
            "results": results,
            "summary": {
                "total": len(results),
                "passed": passed,
                "failed": failed,
                "all_correct": all_correct
            }
        }, f, indent=2)
    
    print(f"\nResults saved to: test_custom_instructions_results.json")
    
    return results

if __name__ == "__main__":
    main()

