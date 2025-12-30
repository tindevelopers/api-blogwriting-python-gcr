#!/usr/bin/env python3
"""
Test AI Gateway Connection
Tests if AI requests are reaching through the backend AI Gateway
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Test configuration
BASE_URL = os.getenv("API_URL", "https://blog-writer-api-dev-613248238610.europe-west9.run.app")
TEST_ORG_ID = "test-org-123"
TEST_USER_ID = "test-user-456"

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text:^70}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text: str):
    """Print error message"""
    print(f"{RED}✗ {text}{RESET}")


def print_info(text: str):
    """Print info message"""
    print(f"{YELLOW}ℹ {text}{RESET}")


async def test_health_check():
    """Test 1: Health check endpoint"""
    print_header("Test 1: Health Check")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{BASE_URL}/health")
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"Backend is healthy")
                print_info(f"Status: {data.get('status')}")
                print_info(f"Environment: {data.get('environment')}")
                
                # Check AI Gateway configuration
                if 'ai_gateway' in data:
                    print_info(f"AI Gateway enabled: {data['ai_gateway'].get('enabled')}")
                    print_info(f"AI Gateway URL: {data['ai_gateway'].get('base_url')}")
                
                return True
            else:
                print_error(f"Health check failed: {response.status_code}")
                return False
                
    except Exception as e:
        print_error(f"Health check error: {e}")
        return False


async def test_ai_gateway_generate():
    """Test 2: AI Gateway Content Generation"""
    print_header("Test 2: AI Gateway Content Generation")
    
    test_request = {
        "topic": "Benefits of Python Programming",
        "keywords": ["python", "programming", "benefits"],
        "org_id": TEST_ORG_ID,
        "user_id": TEST_USER_ID,
        "word_count": 500,
        "tone": "professional",
        "model": "gpt-4o-mini"
    }
    
    print_info(f"Sending request to {BASE_URL}/api/v1/ai-gateway/generate")
    print_info(f"Topic: {test_request['topic']}")
    print_info(f"Model: {test_request['model']}")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            start_time = datetime.now()
            
            response = await client.post(
                f"{BASE_URL}/api/v1/ai-gateway/generate",
                json=test_request,
                headers={"Content-Type": "application/json"}
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"Content generated successfully in {elapsed:.2f}s")
                print_info(f"Content length: {len(data.get('content', ''))} characters")
                print_info(f"Word count: {data.get('word_count', 'N/A')}")
                print_info(f"Quality score: {data.get('quality_score', 'N/A')}/100")
                print_info(f"Model used: {data.get('model_used', 'N/A')}")
                
                if data.get('ai_polished'):
                    print_info(f"Content was AI polished")
                
                # Show first 200 characters of content
                content_preview = data.get('content', '')[:200]
                print(f"\n{YELLOW}Content preview:{RESET}")
                print(content_preview + "...")
                
                return True
            else:
                print_error(f"Generation failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                return False
                
    except httpx.TimeoutException:
        print_error(f"Request timed out after 120 seconds")
        return False
    except Exception as e:
        print_error(f"Generation error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_ai_gateway_polish():
    """Test 3: AI Gateway Content Polishing"""
    print_header("Test 3: AI Gateway Content Polishing")
    
    test_content = """
    <thinking>This is a test artifact that should be removed</thinking>
    
    # Test Blog Post
    
    This is a sample blog post with some content that needs polishing.
    It might have some [TODO] placeholders and other issues.
    
    ## Section 1
    Content here needs improvement.
    
    <reflection>Internal thoughts that should be stripped</reflection>
    """
    
    test_request = {
        "content": test_content,
        "instructions": "Remove artifacts and improve readability",
        "org_id": TEST_ORG_ID,
        "user_id": TEST_USER_ID
    }
    
    print_info(f"Sending polish request")
    print_info(f"Original length: {len(test_content)} characters")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BASE_URL}/api/v1/ai-gateway/polish",
                json=test_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success("Content polished successfully")
                print_info(f"Original length: {data.get('original_length', 0)}")
                print_info(f"Polished length: {data.get('polished_length', 0)}")
                print_info(f"Artifacts removed: {data.get('artifacts_removed', 0)} chars")
                print_info(f"AI polished: {data.get('ai_polished', False)}")
                
                return True
            else:
                print_error(f"Polishing failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print_error(f"Polish error: {e}")
        return False


async def test_ai_gateway_quality_check():
    """Test 4: AI Gateway Quality Check"""
    print_header("Test 4: AI Gateway Quality Check")
    
    test_content = """
    # Sample Blog Post
    
    This is an introduction paragraph that explains what the post is about.
    
    ## First Section
    
    Content for the first section with proper structure and formatting.
    
    ## Second Section
    
    More content here that is properly formatted and structured.
    
    ## Conclusion
    
    A proper conclusion that wraps up the post.
    """
    
    print_info(f"Checking quality of {len(test_content)} character content")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/api/v1/ai-gateway/quality-check",
                json={"content": test_content},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success("Quality check completed")
                print_info(f"Quality score: {data.get('quality_score', 'N/A')}/100")
                print_info(f"Quality grade: {data.get('quality_grade', 'N/A')}")
                print_info(f"Word count: {data.get('word_count', 'N/A')}")
                print_info(f"H2 count: {data.get('h2_count', 'N/A')}")
                
                issues = data.get('issues', [])
                if issues:
                    print_info(f"Found {len(issues)} issues:")
                    for issue in issues:
                        print(f"  - [{issue.get('severity')}] {issue.get('message')}")
                else:
                    print_success("No quality issues found")
                
                return True
            else:
                print_error(f"Quality check failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print_error(f"Quality check error: {e}")
        return False


async def test_ai_gateway_meta_tags():
    """Test 5: AI Gateway Meta Tag Generation"""
    print_header("Test 5: AI Gateway Meta Tag Generation")
    
    test_request = {
        "content": "Sample blog content about Python programming...",
        "title": "Python Programming Guide",
        "keywords": ["python", "programming", "tutorial"],
        "org_id": TEST_ORG_ID,
        "user_id": TEST_USER_ID
    }
    
    print_info(f"Generating meta tags for: {test_request['title']}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BASE_URL}/api/v1/ai-gateway/meta-tags",
                json=test_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success("Meta tags generated successfully")
                print_info(f"Title: {data.get('title', 'N/A')}")
                print_info(f"Description: {data.get('description', 'N/A')[:80]}...")
                print_info(f"OG Title: {data.get('og_title', 'N/A')}")
                
                return True
            else:
                print_error(f"Meta tag generation failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print_error(f"Meta tag generation error: {e}")
        return False


async def check_litellm_configuration():
    """Test 6: Check LiteLLM Configuration"""
    print_header("Test 6: LiteLLM Configuration Check")
    
    print_info("Checking if LiteLLM is configured...")
    
    # Try to read env variables
    litellm_url = os.getenv("LITELLM_PROXY_URL")
    litellm_key = os.getenv("LITELLM_API_KEY")
    
    if litellm_url:
        print_success(f"LITELLM_PROXY_URL is set: {litellm_url}")
    else:
        print_error("LITELLM_PROXY_URL is not set")
    
    if litellm_key:
        print_success("LITELLM_API_KEY is set")
    else:
        print_error("LITELLM_API_KEY is not set")
    
    # Check if backend reports LiteLLM status
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                data = response.json()
                if 'ai_gateway' in data:
                    gateway_info = data['ai_gateway']
                    print_info(f"Backend AI Gateway status:")
                    for key, value in gateway_info.items():
                        print(f"  {key}: {value}")
    except Exception as e:
        print_error(f"Could not check backend LiteLLM status: {e}")


async def run_all_tests():
    """Run all tests"""
    print(f"\n{GREEN}{'='*70}{RESET}")
    print(f"{GREEN}AI Gateway Connection Test Suite{RESET}")
    print(f"{GREEN}{'='*70}{RESET}")
    print(f"{YELLOW}Testing backend: {BASE_URL}{RESET}")
    print(f"{YELLOW}Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    
    results = {}
    
    # Run tests
    results['health'] = await test_health_check()
    await asyncio.sleep(1)
    
    results['litellm_config'] = True  # This is just informational
    await check_litellm_configuration()
    await asyncio.sleep(1)
    
    results['generate'] = await test_ai_gateway_generate()
    await asyncio.sleep(2)
    
    results['polish'] = await test_ai_gateway_polish()
    await asyncio.sleep(1)
    
    results['quality'] = await test_ai_gateway_quality_check()
    await asyncio.sleep(1)
    
    results['meta_tags'] = await test_ai_gateway_meta_tags()
    
    # Print summary
    print_header("Test Summary")
    
    total = len([k for k in results.keys() if k != 'litellm_config'])
    passed = sum(1 for k, v in results.items() if v and k != 'litellm_config')
    
    for test_name, passed_test in results.items():
        if test_name == 'litellm_config':
            continue
        if passed_test:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
    
    print(f"\n{BLUE}Results: {passed}/{total} tests passed{RESET}")
    
    if passed == total:
        print(f"\n{GREEN}✓ All tests passed! AI requests are successfully reaching your backend.{RESET}")
        return 0
    else:
        print(f"\n{RED}✗ Some tests failed. Check the errors above.{RESET}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)

