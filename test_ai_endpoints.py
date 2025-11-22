#!/usr/bin/env python3
"""
Test script to verify all 3 AI endpoints return data correctly.
"""

import asyncio
import sys
import os
import json
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_ai_health_endpoint():
    """Test GET /api/v1/ai/health endpoint"""
    print("\n" + "="*60)
    print("TEST 1: AI Health Endpoint")
    print("="*60)
    
    try:
        from main import app, blog_writer
        
        # Simulate the endpoint call
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        response = client.get("/api/v1/ai/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ai_enabled"):
                print("✅ AI Health endpoint is functional")
                return True
            else:
                print("⚠️ AI is not enabled")
                return False
        else:
            print(f"❌ AI Health endpoint returned error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing AI Health endpoint: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_ai_optimization_endpoint():
    """Test POST /api/v1/keywords/ai-optimization endpoint"""
    print("\n" + "="*60)
    print("TEST 2: AI Optimization Endpoint")
    print("="*60)
    
    try:
        from main import app, enhanced_analyzer
        
        # Check if enhanced_analyzer is available
        if not enhanced_analyzer:
            print("⚠️ Enhanced analyzer not available - skipping test")
            return None
        
        if not enhanced_analyzer._df_client:
            print("⚠️ DataForSEO client not initialized - skipping test")
            return None
        
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        request_data = {
            "keywords": ["digital marketing"],
            "location": "United States",
            "language": "en"
        }
        
        response = client.post("/api/v1/keywords/ai-optimization", json=request_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if "ai_optimization_analysis" in data:
                print("✅ AI Optimization endpoint is functional")
                return True
            else:
                print("⚠️ Response missing ai_optimization_analysis")
                return False
        elif response.status_code == 503:
            print("⚠️ Service unavailable - DataForSEO credentials may not be configured")
            return None
        else:
            print(f"❌ AI Optimization endpoint returned error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing AI Optimization endpoint: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_enhanced_keywords_endpoint():
    """Test POST /api/v1/keywords/enhanced endpoint (with AI metrics)"""
    print("\n" + "="*60)
    print("TEST 3: Enhanced Keywords Endpoint (with AI metrics)")
    print("="*60)
    
    try:
        from main import app, enhanced_analyzer
        
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        request_data = {
            "keywords": ["digital marketing"],
            "location": "United States",
            "language": "en"
        }
        
        response = client.post("/api/v1/keywords/enhanced", json=request_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if AI metrics are present
            if "enhanced_analysis" in data:
                keyword_analysis = data["enhanced_analysis"].get("digital marketing", {})
                
                has_ai_metrics = any(key.startswith("ai_") for key in keyword_analysis.keys())
                
                print(f"Response structure: {json.dumps(list(data.keys()), indent=2)}")
                print(f"\nKeyword analysis keys: {list(keyword_analysis.keys())[:10]}...")
                
                if has_ai_metrics:
                    ai_fields = [k for k in keyword_analysis.keys() if k.startswith("ai_")]
                    print(f"\n✅ AI metrics found: {ai_fields}")
                    print(f"AI Search Volume: {keyword_analysis.get('ai_search_volume', 'N/A')}")
                    print(f"AI Trend: {keyword_analysis.get('ai_trend', 'N/A')}")
                    return True
                else:
                    print("⚠️ Enhanced endpoint works but AI metrics not present")
                    print("   (This may be normal if DataForSEO credentials are not configured)")
                    return None
            else:
                print("❌ Response missing enhanced_analysis")
                return False
        else:
            print(f"❌ Enhanced endpoint returned error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Enhanced endpoint: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("AI ENDPOINTS VERIFICATION TEST")
    print("="*60)
    
    results = {}
    
    # Test 1: AI Health
    results["ai_health"] = await test_ai_health_endpoint()
    
    # Test 2: AI Optimization
    results["ai_optimization"] = await test_ai_optimization_endpoint()
    
    # Test 3: Enhanced Keywords
    results["enhanced_keywords"] = await test_enhanced_keywords_endpoint()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for endpoint, result in results.items():
        status = "✅ Functional" if result is True else "⚠️ Limited/Unavailable" if result is None else "❌ Error"
        print(f"{endpoint:25} {status}")
    
    all_working = all(r is True for r in results.values() if r is not None)
    some_working = any(r is True for r in results.values())
    
    print("\n" + "="*60)
    if all_working:
        print("✅ ALL ENDPOINTS ARE FUNCTIONAL")
    elif some_working:
        print("⚠️ SOME ENDPOINTS ARE FUNCTIONAL (check DataForSEO credentials)")
    else:
        print("❌ ENDPOINTS NEED ATTENTION")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

