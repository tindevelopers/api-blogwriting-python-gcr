#!/usr/bin/env python3
"""
test_new_features.py
Test script for new blog generation features:
- include_eeat parameter (optional, default false)
- additional_resources parameter
- Word count enforcement (SHORT: 800, MEDIUM: 1500, LONG: 2500, EXTENDED: 4000)
- Conclusion and Additional Resources sections
- Section-by-section writing with link placement
"""

import os
import sys
import requests
import json
import re
from typing import Dict, Any, Optional

# Configuration
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
ENDPOINT = f"{BASE_URL}/api/v1/blog/generate-enhanced"
TIMEOUT = 300

# Colors for output
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
CYAN = '\033[0;36m'
NC = '\033[0m'  # No Color

class TestResult:
    """Simple test result container."""
    def __init__(self, name: str, passed: bool, message: str = ""):
        self.name = name
        self.passed = passed
        self.message = message

def print_test_header(test_name: str):
    """Print a formatted test header."""
    print(f"\n{YELLOW}{'='*60}{NC}")
    print(f"{YELLOW}{test_name}{NC}")
    print(f"{YELLOW}{'='*60}{NC}\n")

def test_eeat_disabled() -> TestResult:
    """Test that E-E-A-T is disabled by default."""
    print_test_header("Test 1: E-E-A-T Disabled by Default")
    
    payload = {
        "topic": "Python Programming Basics",
        "keywords": ["python", "programming", "coding"],
        "tone": "professional",
        "length": "short",
        "word_count_target": 800,
        "blog_type": "tutorial"
    }
    
    try:
        print(f"  Sending request to {ENDPOINT}...")
        response = requests.post(ENDPOINT, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        eeat_score = data.get("quality_dimensions", {}).get("eeat", {}).get("score", 0)
        word_count = data.get("word_count", 0)
        content = data.get("content", "")
        has_conclusion = "## Conclusion" in content
        has_resources = "## Additional Resources" in content
        
        print(f"  Word Count: {word_count} (target: 800)")
        print(f"  E-E-A-T Score: {eeat_score}")
        print(f"  Has Conclusion: {'✅' if has_conclusion else '❌'}")
        print(f"  Has Additional Resources: {'✅' if has_resources else '❌'}")
        
        # E-E-A-T should be neutral (~50.0) when disabled
        if 45 <= eeat_score <= 55:
            return TestResult("E-E-A-T Disabled", True, f"Score is {eeat_score} (expected ~50.0)")
        else:
            return TestResult("E-E-A-T Disabled", False, f"Score is {eeat_score} (expected ~50.0)")
            
    except Exception as e:
        return TestResult("E-E-A-T Disabled", False, f"Error: {str(e)}")

def test_eeat_enabled() -> TestResult:
    """Test that E-E-A-T works when enabled."""
    print_test_header("Test 2: E-E-A-T Enabled")
    
    payload = {
        "topic": "Medical Advice for Diabetes Management",
        "keywords": ["diabetes", "medical advice", "health"],
        "tone": "professional",
        "length": "medium",
        "word_count_target": 1500,
        "blog_type": "guide",
        "include_eeat": True
    }
    
    try:
        print(f"  Sending request to {ENDPOINT}...")
        response = requests.post(ENDPOINT, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        eeat_score = data.get("quality_dimensions", {}).get("eeat", {}).get("score", 0)
        word_count = data.get("word_count", 0)
        content = data.get("content", "")
        
        # Check for experience indicators
        experience_pattern = r"\b(I have|In my experience|Based on my|I've|I've been|I've seen|I've found)\b"
        experience_matches = re.findall(experience_pattern, content, re.IGNORECASE)
        has_experience = len(experience_matches) > 0
        
        print(f"  Word Count: {word_count} (target: 1500)")
        print(f"  E-E-A-T Score: {eeat_score}")
        print(f"  Experience Indicators Found: {len(experience_matches)}")
        if experience_matches:
            print(f"  Examples: {', '.join(experience_matches[:3])}")
        
        if eeat_score > 50 and has_experience:
            return TestResult("E-E-A-T Enabled", True, 
                            f"Score is {eeat_score} (>50) and experience indicators found")
        elif eeat_score > 50:
            return TestResult("E-E-A-T Enabled", True, 
                            f"Score is {eeat_score} (>50) but no experience indicators found")
        else:
            return TestResult("E-E-A-T Enabled", False, 
                            f"Score is {eeat_score} (expected >50)")
            
    except Exception as e:
        return TestResult("E-E-A-T Enabled", False, f"Error: {str(e)}")

def test_additional_resources() -> TestResult:
    """Test that additional resources are included when provided."""
    print_test_header("Test 3: Additional Resources")
    
    payload = {
        "topic": "Web Development Best Practices",
        "keywords": ["web development", "best practices", "coding"],
        "tone": "professional",
        "length": "short",
        "word_count_target": 800,
        "blog_type": "guide",
        "additional_resources": [
            {
                "title": "MDN Web Docs",
                "url": "https://developer.mozilla.org",
                "description": "Comprehensive web development documentation"
            },
            {
                "title": "W3C Standards",
                "url": "https://www.w3.org",
                "description": "Web standards and guidelines"
            }
        ]
    }
    
    try:
        print(f"  Sending request to {ENDPOINT}...")
        response = requests.post(ENDPOINT, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        content = data.get("content", "")
        has_resources = "## Additional Resources" in content
        has_mdn = "developer.mozilla.org" in content
        has_w3c = "www.w3.org" in content
        
        print(f"  Has Additional Resources Section: {'✅' if has_resources else '❌'}")
        print(f"  Contains MDN link: {'✅' if has_mdn else '❌'}")
        print(f"  Contains W3C link: {'✅' if has_w3c else '❌'}")
        
        if has_resources:
            return TestResult("Additional Resources", True, "Resources section found")
        else:
            return TestResult("Additional Resources", False, "Resources section not found")
            
    except Exception as e:
        return TestResult("Additional Resources", False, f"Error: {str(e)}")

def test_word_counts() -> list:
    """Test word count targets for all length options."""
    print_test_header("Test 4: Word Count Enforcement")
    
    targets = {
        "short": 800,
        "medium": 1500,
        "long": 2500,
        "extended": 4000
    }
    
    results = []
    
    for length, target in targets.items():
        payload = {
            "topic": f"Test Topic for {length} content",
            "keywords": ["test", "topic"],
            "tone": "professional",
            "length": length,
            "blog_type": "guide"
        }
        
        try:
            print(f"  Testing {length} (target: {target} words)...")
            response = requests.post(ENDPOINT, json=payload, timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            word_count = data.get("word_count", 0)
            percentage = (word_count / target) * 100
            
            print(f"    Word Count: {word_count}")
            print(f"    Percentage: {percentage:.1f}%")
            
            if percentage >= 80:
                results.append(TestResult(f"Word Count ({length})", True, 
                                        f"{word_count} words ({percentage:.1f}%)"))
                print(f"    Status: {GREEN}✅ PASS{NC}")
            else:
                results.append(TestResult(f"Word Count ({length})", False, 
                                        f"{word_count} words ({percentage:.1f}%) - need at least 80%"))
                print(f"    Status: {RED}❌ FAIL{NC}")
                
        except Exception as e:
            results.append(TestResult(f"Word Count ({length})", False, f"Error: {str(e)}"))
            print(f"    Status: {RED}❌ ERROR{NC}: {str(e)}")
    
    return results

def test_structure() -> TestResult:
    """Test that conclusion and additional resources sections exist and conclusion has no links."""
    print_test_header("Test 5: Content Structure")
    
    payload = {
        "topic": "Web Development Fundamentals",
        "keywords": ["web development", "fundamentals"],
        "tone": "professional",
        "length": "short",
        "blog_type": "guide"
    }
    
    try:
        print(f"  Sending request to {ENDPOINT}...")
        response = requests.post(ENDPOINT, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        content = data.get("content", "")
        has_conclusion = "## Conclusion" in content
        has_resources = "## Additional Resources" in content
        
        # Extract conclusion section and check for links
        conclusion_match = re.search(r"## Conclusion(.*?)(## Additional Resources|$)", content, re.DOTALL)
        links_in_conclusion = 0
        if conclusion_match:
            conclusion_text = conclusion_match.group(1)
            links_in_conclusion = len(re.findall(r"\[.*?\]\(.*?\)", conclusion_text))
        
        print(f"  Has Conclusion Section: {'✅' if has_conclusion else '❌'}")
        print(f"  Has Additional Resources Section: {'✅' if has_resources else '❌'}")
        print(f"  Links in Conclusion: {links_in_conclusion} (should be 0)")
        
        if has_conclusion and has_resources and links_in_conclusion == 0:
            return TestResult("Content Structure", True, 
                            "All structure requirements met")
        else:
            issues = []
            if not has_conclusion:
                issues.append("missing conclusion")
            if not has_resources:
                issues.append("missing resources")
            if links_in_conclusion > 0:
                issues.append(f"{links_in_conclusion} links in conclusion")
            return TestResult("Content Structure", False, ", ".join(issues))
            
    except Exception as e:
        return TestResult("Content Structure", False, f"Error: {str(e)}")

def test_link_placement() -> TestResult:
    """Test that internal links are placed correctly (not in conclusion)."""
    print_test_header("Test 6: Link Placement")
    
    payload = {
        "topic": "SEO Optimization Techniques",
        "keywords": ["SEO", "optimization", "search engine"],
        "tone": "professional",
        "length": "medium",
        "word_count_target": 1500,
        "blog_type": "guide",
        "site_domain": "example.com",
        "internal_link_targets": [
            {"slug": "seo-basics", "title": "SEO Basics"},
            {"slug": "keyword-research", "title": "Keyword Research"},
            {"slug": "content-optimization", "title": "Content Optimization"}
        ]
    }
    
    try:
        print(f"  Sending request to {ENDPOINT}...")
        response = requests.post(ENDPOINT, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        content = data.get("content", "")
        
        # Count internal links
        internal_links = len(re.findall(r"example\.com", content))
        
        # Check conclusion section for links
        conclusion_match = re.search(r"## Conclusion(.*?)(## Additional Resources|$)", content, re.DOTALL)
        links_in_conclusion = 0
        if conclusion_match:
            conclusion_text = conclusion_match.group(1)
            links_in_conclusion = len(re.findall(r"\[.*?\]\(.*?\)", conclusion_text))
        
        print(f"  Internal links found: {internal_links}")
        print(f"  Links in conclusion: {links_in_conclusion} (should be 0)")
        
        if links_in_conclusion == 0:
            return TestResult("Link Placement", True, 
                            f"{internal_links} internal links, none in conclusion")
        else:
            return TestResult("Link Placement", False, 
                            f"{links_in_conclusion} links found in conclusion")
            
    except Exception as e:
        return TestResult("Link Placement", False, f"Error: {str(e)}")

def main():
    """Run all tests and print summary."""
    print(f"{BLUE}{'='*60}{NC}")
    print(f"{BLUE}Blog Generation Feature Tests{NC}")
    print(f"{BLUE}{'='*60}{NC}")
    print(f"\n{CYAN}Base URL: {BASE_URL}{NC}")
    print(f"{CYAN}Endpoint: {ENDPOINT}{NC}\n")
    
    results = []
    
    # Run tests
    results.append(test_eeat_disabled())
    results.append(test_eeat_enabled())
    results.append(test_additional_resources())
    results.extend(test_word_counts())
    results.append(test_structure())
    results.append(test_link_placement())
    
    # Print summary
    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}Test Summary{NC}")
    print(f"{BLUE}{'='*60}{NC}\n")
    
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    
    for result in results:
        status = f"{GREEN}✅ PASS{NC}" if result.passed else f"{RED}❌ FAIL{NC}"
        print(f"  {status} {result.name}")
        if result.message:
            print(f"      {result.message}")
    
    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"Total: {passed}/{total} tests passed")
    if passed == total:
        print(f"{GREEN}✅ All tests passed!{NC}")
        return 0
    else:
        print(f"{RED}❌ Some tests failed{NC}")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Tests interrupted by user{NC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Unexpected error: {str(e)}{NC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
