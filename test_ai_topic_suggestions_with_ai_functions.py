#!/usr/bin/env python3
"""
Test script for AI Topic Suggestions endpoint with AI functions enabled.
Tests the endpoint with include_ai_search_volume and include_llm_mentions enabled.
"""

import json
import sys
import os
from typing import Dict, Any

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: 'requests' module not available. Install with: pip install requests")

# Configuration
BASE_URL = os.getenv("API_BASE_URL", "https://blog-writer-api-dev-kq42l26tuq-od.a.run.app")
ENDPOINT = "/api/v1/keywords/ai-topic-suggestions"

def make_request(payload: Dict[str, Any]) -> tuple[int, Dict[str, Any] | str]:
    """Make HTTP request using requests or curl."""
    if REQUESTS_AVAILABLE:
        try:
            response = requests.post(
                f"{BASE_URL}{ENDPOINT}",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120
            )
            if response.status_code == 200:
                return response.status_code, response.json()
            return response.status_code, response.text
        except requests.exceptions.RequestException as e:
            return 0, str(e)
    else:
        # Fallback to curl
        import subprocess
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(payload, f)
            temp_file = f.name
        
        try:
            result = subprocess.run(
                ['curl', '-s', '-X', 'POST', 
                 f'{BASE_URL}{ENDPOINT}',
                 '-H', 'Content-Type: application/json',
                 '-d', f'@{temp_file}',
                 '--max-time', '120'],
                capture_output=True,
                text=True
            )
            os.unlink(temp_file)
            
            if result.returncode == 0:
                try:
                    return 200, json.loads(result.stdout)
                except json.JSONDecodeError:
                    return 200, result.stdout
            else:
                return 0, result.stderr
        except Exception as e:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            return 0, str(e)


def test_with_keywords():
    """Test endpoint with keywords parameter."""
    print("\n" + "="*80)
    print("TEST 1: Testing with keywords parameter")
    print("="*80)
    
    payload = {
        "keywords": ["concrete remediation", "foundation repair"],
        "location": "United States",
        "language": "en",
        "include_ai_search_volume": True,
        "include_llm_mentions": True,
        "include_llm_responses": False,
        "limit": 20
    }
    
    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        status_code, response_data = make_request(payload)
        
        print(f"\nStatus Code: {status_code}")
        
        if status_code == 200 and isinstance(response_data, dict):
            data = response_data
            print(f"\n✅ Success!")
            print(f"\nResponse Summary:")
            print(f"  - Seed Keywords: {data.get('seed_keywords', [])}")
            print(f"  - Location: {data.get('location', 'N/A')}")
            print(f"  - Total Suggestions: {data.get('summary', {}).get('total_suggestions', 0)}")
            print(f"  - High Priority Topics: {data.get('summary', {}).get('high_priority_topics', 0)}")
            print(f"  - Trending Topics: {data.get('summary', {}).get('trending_topics', 0)}")
            
            # Check AI metrics
            ai_metrics = data.get('ai_metrics', {})
            if ai_metrics.get('search_volume'):
                print(f"\n✅ AI Search Volume Data Available:")
                sv_data = ai_metrics['search_volume']
                for keyword, metrics in list(sv_data.items())[:5]:
                    print(f"  - {keyword}: {metrics.get('ai_search_volume', 0):,} AI searches")
            
            if ai_metrics.get('llm_mentions'):
                print(f"\n✅ LLM Mentions Data Available:")
                mentions_data = ai_metrics['llm_mentions']
                for keyword, mentions in list(mentions_data.items())[:3]:
                    mentions_count = mentions.get('mentions_count', 0) if isinstance(mentions, dict) else 0
                    print(f"  - {keyword}: {mentions_count} mentions")
            
            # Show sample topic suggestions
            topic_suggestions = data.get('topic_suggestions', [])
            if topic_suggestions:
                print(f"\n📝 Sample Topic Suggestions (first 5):")
                for i, topic in enumerate(topic_suggestions[:5], 1):
                    print(f"\n  {i}. {topic.get('topic', 'N/A')}")
                    print(f"     - Source Keyword: {topic.get('source_keyword', 'N/A')}")
                    print(f"     - Search Volume: {topic.get('search_volume', 0):,}")
                    print(f"     - AI Search Volume: {topic.get('ai_search_volume', 0):,}")
                    print(f"     - Difficulty: {topic.get('difficulty', 0):.1f}")
                    print(f"     - Ranking Score: {topic.get('ranking_score', 0):.1f}")
                    print(f"     - Opportunity Score: {topic.get('opportunity_score', 0):.1f}")
                    if topic.get('ai_optimization_score') is not None:
                        print(f"     - AI Optimization Score: {topic.get('ai_optimization_score', 0)}/100")
                    if topic.get('reason'):
                        print(f"     - Reason: {topic.get('reason', '')[:100]}...")
            
            # Save full response
            with open('test_ai_topic_suggestions_keywords.json', 'w') as f:
                json.dump(data, f, indent=2)
            print(f"\n💾 Full response saved to: test_ai_topic_suggestions_keywords.json")
            
        else:
            print(f"\n❌ Error: {status_code}")
            print(f"Response: {response_data}")
            return False
            
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        return False
    
    return status_code == 200


def test_with_content_objective():
    """Test endpoint with content_objective parameter."""
    print("\n" + "="*80)
    print("TEST 2: Testing with content_objective parameter")
    print("="*80)
    
    payload = {
        "content_objective": "I want to write articles about concrete remediation and foundation repair for homeowners",
        "target_audience": "general consumers",
        "industry": "Construction",
        "content_goals": ["SEO & Rankings", "Engagement"],
        "location": "United States",
        "language": "en",
        "include_ai_search_volume": True,
        "include_llm_mentions": True,
        "include_llm_responses": False,
        "limit": 20
    }
    
    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        status_code, response_data = make_request(payload)
        
        print(f"\nStatus Code: {status_code}")
        
        if status_code == 200 and isinstance(response_data, dict):
            data = response_data
            print(f"\n✅ Success!")
            print(f"\nResponse Summary:")
            print(f"  - Extracted Keywords: {data.get('seed_keywords', [])}")
            print(f"  - Content Objective: {data.get('content_objective', 'N/A')}")
            print(f"  - Target Audience: {data.get('target_audience', 'N/A')}")
            print(f"  - Industry: {data.get('industry', 'N/A')}")
            print(f"  - Total Suggestions: {data.get('summary', {}).get('total_suggestions', 0)}")
            
            # Check AI metrics
            ai_metrics = data.get('ai_metrics', {})
            if ai_metrics.get('search_volume'):
                print(f"\n✅ AI Search Volume Data Available:")
                sv_data = ai_metrics['search_volume']
                for keyword, metrics in list(sv_data.items())[:5]:
                    print(f"  - {keyword}: {metrics.get('ai_search_volume', 0):,} AI searches")
            
            if ai_metrics.get('llm_mentions'):
                print(f"\n✅ LLM Mentions Data Available:")
                mentions_data = ai_metrics['llm_mentions']
                for keyword, mentions in list(mentions_data.items())[:3]:
                    mentions_count = mentions.get('mentions_count', 0) if isinstance(mentions, dict) else 0
                    print(f"  - {keyword}: {mentions_count} mentions")
            
            # Show sample topic suggestions
            topic_suggestions = data.get('topic_suggestions', [])
            if topic_suggestions:
                print(f"\n📝 Sample Topic Suggestions (first 5):")
                for i, topic in enumerate(topic_suggestions[:5], 1):
                    print(f"\n  {i}. {topic.get('topic', 'N/A')}")
                    print(f"     - Source Keyword: {topic.get('source_keyword', 'N/A')}")
                    print(f"     - Search Volume: {topic.get('search_volume', 0):,}")
                    print(f"     - AI Search Volume: {topic.get('ai_search_volume', 0):,}")
                    print(f"     - Difficulty: {topic.get('difficulty', 0):.1f}")
                    print(f"     - Ranking Score: {topic.get('ranking_score', 0):.1f}")
                    print(f"     - Opportunity Score: {topic.get('opportunity_score', 0):.1f}")
                    if topic.get('ai_optimization_score') is not None:
                        print(f"     - AI Optimization Score: {topic.get('ai_optimization_score', 0)}/100")
                    if topic.get('reason'):
                        print(f"     - Reason: {topic.get('reason', '')[:100]}...")
            
            # Save full response
            with open('test_ai_topic_suggestions_content_objective.json', 'w') as f:
                json.dump(data, f, indent=2)
            print(f"\n💾 Full response saved to: test_ai_topic_suggestions_content_objective.json")
            
        else:
            print(f"\n❌ Error: {status_code}")
            print(f"Response: {response_data}")
            return False
            
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        return False
    
    return status_code == 200


def test_with_ai_functions_disabled():
    """Test endpoint with AI functions disabled for comparison."""
    print("\n" + "="*80)
    print("TEST 3: Testing with AI functions DISABLED (for comparison)")
    print("="*80)
    
    payload = {
        "keywords": ["concrete remediation"],
        "location": "United States",
        "language": "en",
        "include_ai_search_volume": False,
        "include_llm_mentions": False,
        "include_llm_responses": False,
        "limit": 10
    }
    
    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        status_code, response_data = make_request(payload)
        
        print(f"\nStatus Code: {status_code}")
        
        if status_code == 200 and isinstance(response_data, dict):
            data = response_data
            print(f"\n✅ Success!")
            print(f"\nResponse Summary:")
            print(f"  - Total Suggestions: {data.get('summary', {}).get('total_suggestions', 0)}")
            
            # Check AI metrics (should be empty or minimal)
            ai_metrics = data.get('ai_metrics', {})
            if not ai_metrics.get('search_volume') and not ai_metrics.get('llm_mentions'):
                print(f"\n✅ AI functions correctly disabled (no AI metrics)")
            else:
                print(f"\n⚠️  Warning: AI metrics present even though disabled")
            
            # Show sample topic suggestions
            topic_suggestions = data.get('topic_suggestions', [])
            if topic_suggestions:
                print(f"\n📝 Sample Topic Suggestions (first 3):")
                for i, topic in enumerate(topic_suggestions[:3], 1):
                    print(f"\n  {i}. {topic.get('topic', 'N/A')}")
                    print(f"     - Source Keyword: {topic.get('source_keyword', 'N/A')}")
                    print(f"     - Search Volume: {topic.get('search_volume', 0):,}")
                    print(f"     - AI Search Volume: {topic.get('ai_search_volume', 0):,} (should be 0)")
            
        else:
            print(f"\n❌ Error: {status_code}")
            print(f"Response: {response_data}")
            return False
            
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        return False
    
    return status_code == 200


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("AI TOPIC SUGGESTIONS ENDPOINT TEST - WITH AI FUNCTIONS")
    print("="*80)
    print(f"\nBase URL: {BASE_URL}")
    print(f"Endpoint: {ENDPOINT}")
    
    results = []
    
    # Test 1: With keywords
    results.append(("Test 1: Keywords with AI functions", test_with_keywords()))
    
    # Test 2: With content objective
    results.append(("Test 2: Content objective with AI functions", test_with_content_objective()))
    
    # Test 3: With AI functions disabled (for comparison)
    results.append(("Test 3: AI functions disabled", test_with_ai_functions_disabled()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

