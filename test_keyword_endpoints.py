#!/usr/bin/env python3
"""Test script for keyword search API endpoints only."""

import json
import sys
import subprocess
import time
from datetime import datetime

API_URL = "https://blog-writer-api-dev-613248238610.europe-west9.run.app"

def run_test(name, method, endpoint, data=None, timeout=120):
    """Run a test and return results."""
    print(f"\n{'='*70}")
    print(f"🧪 {name}")
    print(f"{'='*70}")
    print(f"Endpoint: {method} {endpoint}")
    if data:
        print(f"Request: {json.dumps(data, indent=2)}")
    
    cmd = ["curl", "-s", "-X", method, f"{API_URL}{endpoint}"]
    if data:
        cmd.extend(["-H", "Content-Type: application/json", "-d", json.dumps(data)])
    
    start_time = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        elapsed = time.time() - start_time
        
        if result.returncode != 0:
            print(f"❌ FAILED: curl error (exit code {result.returncode})")
            print(f"Error output: {result.stderr[:500]}")
            return False
        
        try:
            response = json.loads(result.stdout)
            print(f"✅ Status: SUCCESS (took {elapsed:.2f}s)")
            return response
        except json.JSONDecodeError:
            print(f"⚠️  Response is not JSON (may be timeout or error)")
            print(f"Response preview: {result.stdout[:500]}")
            return None
    except subprocess.TimeoutExpired:
        print(f"⏱️  TIMEOUT after {timeout}s")
        return None
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def print_keyword_analysis(analysis, keyword):
    """Print formatted keyword analysis results."""
    print(f"\n📊 Analysis for '{keyword}':")
    print(f"  • Search Volume: {analysis.get('search_volume', 0):,}")
    print(f"  • Global Search Volume: {analysis.get('global_search_volume', 0):,}")
    print(f"  • CPC: ${analysis.get('cpc', 0.0):.2f}")
    print(f"  • Competition: {analysis.get('competition', 0.0):.2f}")
    print(f"  • Difficulty: {analysis.get('difficulty', 'N/A')}")
    print(f"  • Difficulty Score: {analysis.get('difficulty_score', 0):.1f}")
    print(f"  • Related Keywords: {len(analysis.get('related_keywords', []))}")
    print(f"  • Long-tail Keywords: {len(analysis.get('long_tail_keywords', []))}")
    if analysis.get('recommended'):
        print(f"  • Recommended: ✅")
        print(f"  • Reason: {analysis.get('reason', 'N/A')}")

def print_enhanced_analysis(analysis, keyword):
    """Print formatted enhanced keyword analysis results."""
    print(f"\n📊 Enhanced Analysis for '{keyword}':")
    print(f"  • Search Volume: {analysis.get('search_volume', 0):,}")
    print(f"  • Global Search Volume: {analysis.get('global_search_volume', 0):,}")
    print(f"  • CPC: ${analysis.get('cpc', 0.0):.2f}")
    print(f"  • Competition: {analysis.get('competition', 0.0):.2f}")
    print(f"  • Difficulty: {analysis.get('difficulty', 'N/A')}")
    print(f"  • Difficulty Score: {analysis.get('difficulty_score', 0):.1f}")
    clicks = analysis.get('clicks', 0) or 0
    cps = analysis.get('cps', 0.0) or 0.0
    trend_score = analysis.get('trend_score', 0.0) or 0.0
    print(f"  • Clicks: {clicks:,}")
    print(f"  • CPS: {cps:.2f}")
    print(f"  • Trend Score: {trend_score:.2f}")
    
    # Related keywords enhanced
    related = analysis.get('related_keywords_enhanced', [])
    if related:
        print(f"  • Related Keywords (Enhanced): {len(related)}")
        for rk in related[:3]:
            print(f"    - {rk.get('keyword', 'N/A')}: Vol={rk.get('search_volume', 0):,}, CPC=${rk.get('cpc', 0.0):.2f}")
    
    # Questions
    questions = analysis.get('questions', [])
    if questions:
        print(f"  • Questions: {len(questions)}")
        for q in questions[:2]:
            print(f"    - {q.get('keyword', 'N/A')}: Vol={q.get('search_volume', 0):,}")
    
    # Topics
    topics = analysis.get('topics', [])
    if topics:
        print(f"  • Topics: {len(topics)}")
        for t in topics[:2]:
            print(f"    - {t.get('keyword', 'N/A')}: Vol={t.get('search_volume', 0):,}")

# Test Results Tracking
test_results = []

print("\n" + "="*70)
print("🔍 KEYWORD SEARCH ENDPOINTS TEST SUITE")
print("="*70)
print(f"API URL: {API_URL}")
print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)

# Test 1: Standard Keyword Analysis
print("\n\n")
test1 = run_test(
    "Test 1: Standard Keyword Analysis",
    "POST",
    "/api/v1/keywords/analyze",
    {
        "keywords": ["pet grooming", "dog care"],
        "location": "United States",
        "language": "en"
    }
)
if test1:
    ka = test1.get('keyword_analysis', {})
    print(f"\n✅ Keywords analyzed: {len(ka)}")
    for kw, analysis in list(ka.items())[:2]:
        print_keyword_analysis(analysis, kw)
    test_results.append(("Test 1: Standard Keyword Analysis", True))
else:
    test_results.append(("Test 1: Standard Keyword Analysis", False))

# Test 2: Enhanced Keyword Analysis (Single Keyword)
print("\n\n")
test2 = run_test(
    "Test 2: Enhanced Keyword Analysis (Single Keyword)",
    "POST",
    "/api/v1/keywords/enhanced",
    {
        "keywords": ["pet grooming"],
        "location": "United States",
        "language": "en",
        "max_suggestions_per_keyword": 10
    },
    timeout=180
)
if test2:
    ea = test2.get('enhanced_analysis', {})
    print(f"\n✅ Keywords analyzed: {len(ea)}")
    cs = test2.get('cluster_summary', {})
    print(f"  • Clusters: {cs.get('cluster_count', 0)}")
    print(f"  • Total keywords: {test2.get('total_keywords', 0)}")
    for kw, analysis in list(ea.items())[:1]:
        print_enhanced_analysis(analysis, kw)
    test_results.append(("Test 2: Enhanced Keyword Analysis (Single)", True))
else:
    test_results.append(("Test 2: Enhanced Keyword Analysis (Single)", False))

# Test 3: Enhanced Keyword Analysis (Multiple Keywords)
print("\n\n")
test3 = run_test(
    "Test 3: Enhanced Keyword Analysis (Multiple Keywords)",
    "POST",
    "/api/v1/keywords/enhanced",
    {
        "keywords": ["python programming", "web development"],
        "location": "United States",
        "language": "en",
        "max_suggestions_per_keyword": 5
    },
    timeout=180
)
if test3:
    ea = test3.get('enhanced_analysis', {})
    print(f"\n✅ Keywords analyzed: {len(ea)}")
    for kw in list(ea.keys())[:2]:
        analysis = ea[kw]
        print(f"\n  • {kw}: Vol={analysis.get('search_volume', 0):,}, CPC=${analysis.get('cpc', 0.0):.2f}, Diff={analysis.get('difficulty_score', 0):.1f}")
    test_results.append(("Test 3: Enhanced Keyword Analysis (Multiple)", True))
else:
    test_results.append(("Test 3: Enhanced Keyword Analysis (Multiple)", False))

# Test 4: Keyword Extraction from Content
print("\n\n")
test4 = run_test(
    "Test 4: Keyword Extraction from Content",
    "POST",
    "/api/v1/keywords/extract",
    {
        "content": """
        Pet grooming is an essential service for pet owners who want to keep their dogs and cats 
        healthy and clean. Professional groomers provide services like bathing, haircuts, nail trimming, 
        and ear cleaning. Regular grooming helps prevent skin infections, matting, and other health issues. 
        Many pet owners prefer mobile grooming services that come to their home for convenience.
        """,
        "max_keywords": 10,
        "max_ngram": 3,
        "dedup_lim": 0.7
    }
)
if test4:
    ek = test4.get('extracted_keywords', [])
    clusters = test4.get('clusters', [])
    print(f"\n✅ Keywords extracted: {len(ek)}")
    print(f"  • Clusters: {len(clusters)}")
    print(f"  • Top keywords: {', '.join(ek[:5])}")
    if clusters:
        print(f"\n  • Sample cluster:")
        c = clusters[0]
        print(f"    Topic: {c.get('parent_topic', 'N/A')}")
        print(f"    Keywords: {', '.join(c.get('keywords', [])[:5])}")
    test_results.append(("Test 4: Keyword Extraction", True))
else:
    test_results.append(("Test 4: Keyword Extraction", False))

# Test 5: Keyword Suggestions
print("\n\n")
test5 = run_test(
    "Test 5: Keyword Suggestions",
    "POST",
    "/api/v1/keywords/suggest",
    {
        "keyword": "pet grooming"
    }
)
if test5:
    suggestions = test5.get('keyword_suggestions', {})
    print(f"\n✅ Suggestions retrieved")
    if suggestions:
        # Handle both dict and list formats
        if isinstance(suggestions, dict):
            related = suggestions.get('related_keywords', [])
            long_tail = suggestions.get('long_tail_keywords', [])
            questions = suggestions.get('question_keywords', [])
            print(f"  • Related keywords: {len(related)}")
            if related:
                print(f"    Sample: {', '.join(related[:3])}")
            print(f"  • Long-tail keywords: {len(long_tail)}")
            if long_tail:
                print(f"    Sample: {', '.join(long_tail[:3])}")
            print(f"  • Question keywords: {len(questions)}")
            if questions:
                print(f"    Sample: {', '.join(questions[:3])}")
        elif isinstance(suggestions, list):
            print(f"  • Total suggestions: {len(suggestions)}")
            if suggestions:
                print(f"    Sample: {', '.join(str(s) for s in suggestions[:5])}")
        else:
            print(f"  • Suggestions format: {type(suggestions)}")
            print(f"  • Content: {str(suggestions)[:200]}")
    test_results.append(("Test 5: Keyword Suggestions", True))
else:
    test_results.append(("Test 5: Keyword Suggestions", False))

# Test 6: Enhanced Analysis with SERP
print("\n\n")
test6 = run_test(
    "Test 6: Enhanced Analysis with SERP",
    "POST",
    "/api/v1/keywords/enhanced",
    {
        "keywords": ["dog training"],
        "location": "United States",
        "language": "en",
        "include_serp": True,
        "max_suggestions_per_keyword": 5
    },
    timeout=240
)
if test6:
    ea = test6.get('enhanced_analysis', {})
    print(f"\n✅ Keywords analyzed: {len(ea)}")
    for kw, analysis in list(ea.items())[:1]:
        serp = analysis.get('serp_analysis', {})
        if serp:
            print(f"\n  • SERP Analysis for '{kw}':")
            print(f"    Top ranking domains: {len(serp.get('top_ranking_domains', []))}")
            print(f"    Content depth: {serp.get('content_depth', 'N/A')}")
            print(f"    Competition level: {serp.get('competition_level', 'N/A')}")
    test_results.append(("Test 6: Enhanced Analysis with SERP", True))
else:
    test_results.append(("Test 6: Enhanced Analysis with SERP", False))

# Summary
print("\n\n" + "="*70)
print("📊 TEST SUMMARY")
print("="*70)
passed = sum(1 for _, result in test_results if result)
total = len(test_results)
print(f"\nTotal Tests: {total}")
print(f"Passed: {passed} ✅")
print(f"Failed: {total - passed} ❌")
print(f"Success Rate: {(passed/total*100):.1f}%")

print("\nDetailed Results:")
for test_name, result in test_results:
    status = "✅ PASSED" if result else "❌ FAILED"
    print(f"  {status}: {test_name}")

print("\n" + "="*70)
if passed == total:
    print("🎉 All keyword search endpoints are working correctly!")
else:
    print("⚠️  Some tests failed. Please review the output above.")
print("="*70)

