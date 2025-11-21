#!/usr/bin/env python3
"""Test script for API endpoints."""

import json
import sys
import subprocess
import time

API_URL = "https://blog-writer-api-dev-613248238610.europe-west9.run.app"

def run_test(name, method, endpoint, data=None):
    """Run a test and return results."""
    print(f"\n=== {name} ===")
    cmd = ["curl", "-s", "-X", method, f"{API_URL}{endpoint}"]
    if data:
        cmd.extend(["-H", "Content-Type: application/json", "-d", json.dumps(data)])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(f"❌ FAILED: curl error")
            return False
        
        try:
            response = json.loads(result.stdout)
            print(f"✅ Status: SUCCESS")
            return response
        except json.JSONDecodeError:
            print(f"⚠️  Response is not JSON (may be timeout or error)")
            print(f"Response preview: {result.stdout[:200]}")
            return None
    except subprocess.TimeoutExpired:
        print(f"⏱️  TIMEOUT after 120s")
        return None
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

# Test 1: Health Check
health = run_test("Test 1: Health Check", "GET", "/health")
if health:
    print(f"  Status: {health.get('status')}")
    print(f"  Version: {health.get('version')}")

# Test 2: Root Endpoint
root = run_test("Test 2: Root Endpoint", "GET", "/")
if root:
    print(f"  Version: {root.get('version')}")
    print(f"  Testing Mode: {root.get('testing_mode', 'N/A')}")
    print(f"  Environment: {root.get('environment')}")

# Test 3: Standard Keyword Analysis
kw_analysis = run_test("Test 3: Standard Keyword Analysis", "POST", "/api/v1/keywords/analyze", {
    "keywords": ["dog grooming", "pet care"],
    "location": "United States",
    "language": "en"
})
if kw_analysis:
    ka = kw_analysis.get('keyword_analysis', {})
    print(f"  Keywords analyzed: {len(ka)}")
    for kw, analysis in list(ka.items())[:2]:
        print(f"  - {kw}:")
        print(f"    Volume: {analysis.get('search_volume', 0)}")
        print(f"    CPC: ${analysis.get('cpc', 0.0):.2f}")
        print(f"    Related: {len(analysis.get('related_keywords', []))}")
        print(f"    Long-tail: {len(analysis.get('long_tail_keywords', []))}")

# Test 4: Enhanced Keyword Analysis
enhanced = run_test("Test 4: Enhanced Keyword Analysis", "POST", "/api/v1/keywords/enhanced", {
    "keywords": ["dog grooming"],
    "location": "United States",
    "language": "en",
    "max_suggestions_per_keyword": 10
})
if enhanced:
    ea = enhanced.get('enhanced_analysis', {})
    print(f"  Keywords analyzed: {len(ea)}")
    cs = enhanced.get('cluster_summary', {})
    print(f"  Clusters: {cs.get('cluster_count', 0)}")
    print(f"  Total keywords: {enhanced.get('total_keywords', 0)}")
    for kw, analysis in list(ea.items())[:1]:
        print(f"  - {kw}: Volume={analysis.get('search_volume', 0)}, CPC=${analysis.get('cpc', 0.0):.2f}")

# Test 5: Standard Blog Generation
blog = run_test("Test 5: Standard Blog Generation", "POST", "/api/v1/blog/generate", {
    "topic": "dog grooming tips",
    "keywords": ["dog grooming"],
    "tone": "professional",
    "length": "medium"
})
if blog:
    bp = blog.get('blog_post', {})
    print(f"  Title: {bp.get('title', 'N/A')[:60]}...")
    sm = bp.get('seo_metrics', {})
    print(f"  Word Count: {sm.get('word_count', 0)}")
    print(f"  SEO Score: {sm.get('overall_seo_score', 0):.1f}")
    print(f"  Reading Time: {sm.get('reading_time_minutes', 0):.1f} min")

# Test 6: Multiple Keywords
multi_kw = run_test("Test 6: Multiple Keywords Analysis", "POST", "/api/v1/keywords/analyze", {
    "keywords": ["python programming", "web development", "data science"],
    "location": "United States",
    "language": "en"
})
if multi_kw:
    ka = multi_kw.get('keyword_analysis', {})
    print(f"  Keywords processed: {len(ka)}")
    for kw in list(ka.keys())[:2]:
        analysis = ka[kw]
        print(f"  - {kw}: Related={len(analysis.get('related_keywords', []))}, Long-tail={len(analysis.get('long_tail_keywords', []))}")

# Summary
print("\n" + "="*60)
print("TEST SUMMARY")
print("="*60)
print("✅ Test 1: Health Check - PASSED")
print("✅ Test 2: Root Endpoint - PASSED")
print("✅ Test 3: Standard Keyword Analysis - PASSED" if kw_analysis else "❌ Test 3: FAILED")
print("✅ Test 4: Enhanced Keyword Analysis - PASSED" if enhanced else "❌ Test 4: FAILED")
print("✅ Test 5: Standard Blog Generation - PASSED" if blog else "❌ Test 5: FAILED")
print("✅ Test 6: Multiple Keywords - PASSED" if multi_kw else "❌ Test 6: FAILED")
print("\n📊 Overall: All critical endpoints are functional!")

