#!/usr/bin/env python3
"""
Test custom_instructions limit validation using Pydantic models directly.
This tests the validation logic without requiring a running server.
"""

import sys
from pydantic import ValidationError

# Add src to path
sys.path.insert(0, 'src')

from blog_writer_sdk.models.enhanced_blog_models import EnhancedBlogGenerationRequest
from blog_writer_sdk.models.blog_models import BlogRequest

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

def test_enhanced_model(length: int, description: str) -> dict:
    """Test EnhancedBlogGenerationRequest with custom_instructions of given length."""
    custom_instructions = generate_text(length) if length > 0 else None
    
    try:
        request = EnhancedBlogGenerationRequest(
            topic="Test Blog Post",
            keywords=["test", "blogging"],
            custom_instructions=custom_instructions
        )
        actual_length = len(custom_instructions) if custom_instructions else 0
        return {
            "test": description,
            "length": actual_length,
            "status": "✅ PASS",
            "error": None
        }
    except ValidationError as e:
        actual_length = len(custom_instructions) if custom_instructions else 0
        error_msg = str(e.errors()[0]['msg']) if e.errors() else str(e)
        return {
            "test": description,
            "length": actual_length,
            "status": "❌ FAIL",
            "error": error_msg
        }

def test_standard_model(length: int, description: str) -> dict:
    """Test BlogRequest with custom_instructions of given length."""
    custom_instructions = generate_text(length) if length > 0 else None
    
    try:
        request = BlogRequest(
            topic="Test Blog Post",
            keywords=["test", "blogging"],
            custom_instructions=custom_instructions
        )
        actual_length = len(custom_instructions) if custom_instructions else 0
        return {
            "test": description,
            "length": actual_length,
            "status": "✅ PASS",
            "error": None
        }
    except ValidationError as e:
        actual_length = len(custom_instructions) if custom_instructions else 0
        error_msg = str(e.errors()[0]['msg']) if e.errors() else str(e)
        return {
            "test": description,
            "length": actual_length,
            "status": "❌ FAIL",
            "error": error_msg
        }

def main():
    """Run all validation tests."""
    print("🧪 Testing Custom Instructions Limit Validation")
    print("=" * 60)
    print("Testing Pydantic model validation (no server required)")
    print("Expected limit: 5000 characters")
    print("=" * 60)
    print()
    
    enhanced_results = []
    standard_results = []
    
    test_cases = [
        (0, "No custom_instructions"),
        (500, "Small instruction (500 chars)"),
        (1500, "Medium instruction (1500 chars)"),
        (2000, "At old enhanced limit (2000 chars)"),
        (3500, "Between old and new limit (3500 chars)"),
        (5000, "At new limit (5000 chars)"),
        (5001, "Over new limit (5001 chars - should fail)"),
        (10000, "Way over limit (10000 chars - should fail)"),
    ]
    
    print("Testing EnhancedBlogGenerationRequest:")
    print("-" * 60)
    for length, description in test_cases:
        result = test_enhanced_model(length, description)
        enhanced_results.append(result)
        status_icon = "✅" if result["status"] == "✅ PASS" else "❌"
        print(f"{status_icon} {description}")
        print(f"   Length: {result['length']} chars")
        if result["error"]:
            print(f"   Error: {result['error']}")
    
    print()
    print("Testing BlogRequest (Standard):")
    print("-" * 60)
    for length, description in test_cases:
        result = test_standard_model(length, description)
        standard_results.append(result)
        status_icon = "✅" if result["status"] == "✅ PASS" else "❌"
        print(f"{status_icon} {description}")
        print(f"   Length: {result['length']} chars")
        if result["error"]:
            print(f"   Error: {result['error']}")
    
    # Summary
    print()
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    enhanced_passed = sum(1 for r in enhanced_results if r["status"] == "✅ PASS")
    enhanced_failed = sum(1 for r in enhanced_results if r["status"] == "❌ FAIL")
    
    standard_passed = sum(1 for r in standard_results if r["status"] == "✅ PASS")
    standard_failed = sum(1 for r in standard_results if r["status"] == "❌ FAIL")
    
    print(f"\nEnhanced Blog Model:")
    print(f"  ✅ Passed: {enhanced_passed}/{len(enhanced_results)}")
    print(f"  ❌ Failed: {enhanced_failed}/{len(enhanced_results)}")
    
    print(f"\nStandard Blog Model:")
    print(f"  ✅ Passed: {standard_passed}/{len(standard_results)}")
    print(f"  ❌ Failed: {standard_failed}/{len(standard_results)}")
    
    # Expected results
    print()
    print("=" * 60)
    print("EXPECTED BEHAVIOR")
    print("=" * 60)
    print("✅ Should PASS: 0-5000 characters")
    print("❌ Should FAIL: >5000 characters")
    
    # Verify expectations
    print()
    print("=" * 60)
    print("VALIDATION CHECK")
    print("=" * 60)
    
    all_correct = True
    
    # Check enhanced model
    for i, (length, _) in enumerate(test_cases):
        result = enhanced_results[i]
        expected_pass = length <= 5000
        
        if (expected_pass and result["status"] == "✅ PASS") or \
           (not expected_pass and result["status"] == "❌ FAIL"):
            print(f"✅ Enhanced Model - {result['test']}: Correct")
        else:
            print(f"❌ Enhanced Model - {result['test']}: INCORRECT")
            print(f"   Expected: {'PASS' if expected_pass else 'FAIL'}, Got: {result['status']}")
            all_correct = False
    
    # Check standard model
    for i, (length, _) in enumerate(test_cases):
        result = standard_results[i]
        expected_pass = length <= 5000
        
        if (expected_pass and result["status"] == "✅ PASS") or \
           (not expected_pass and result["status"] == "❌ FAIL"):
            print(f"✅ Standard Model - {result['test']}: Correct")
        else:
            print(f"❌ Standard Model - {result['test']}: INCORRECT")
            print(f"   Expected: {'PASS' if expected_pass else 'FAIL'}, Got: {result['status']}")
            all_correct = False
    
    print()
    if all_correct:
        print("🎉 ALL TESTS PASSED - Validation is working correctly!")
    else:
        print("⚠️  SOME TESTS FAILED - Check validation logic")
    
    return {
        "enhanced_results": enhanced_results,
        "standard_results": standard_results,
        "all_correct": all_correct
    }

if __name__ == "__main__":
    results = main()

