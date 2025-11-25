#!/usr/bin/env python3
"""
Standalone test for DataForSEO Content Generation - 100 word blog with subtopics.

This script directly tests the API without requiring the full SDK.
It tests:
1. Generate subtopics from main topic
2. Generate 100-word blog content
3. Generate meta tags

Usage:
    python3 test_100_words_standalone.py
"""

import os
import sys
import asyncio
import httpx
import base64
import json
from typing import Dict, Any

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class DataForSEOTester:
    """Standalone DataForSEO API tester."""
    
    BASE_URL = "https://api.dataforseo.com/v3"
    
    def __init__(self):
        """Initialize with credentials from environment or Google Secret Manager."""
        # Try environment variables first
        self.api_key = os.getenv("DATAFORSEO_API_KEY") or os.getenv("DATAFORSEO_API_LOGIN")
        self.api_secret = os.getenv("DATAFORSEO_API_SECRET") or os.getenv("DATAFORSEO_API_PASSWORD")
        
        # If not in env, try to get from Google Secret Manager
        if not self.api_key or not self.api_secret:
            try:
                import subprocess
                # Try to get from gcloud secrets
                result = subprocess.run(
                    ["gcloud", "secrets", "versions", "access", "latest", "--secret=datforseo-api-key"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    self.api_key = result.stdout.strip()
                
                result = subprocess.run(
                    ["gcloud", "secrets", "versions", "access", "latest", "--secret=datforseo-api-secret"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    self.api_secret = result.stdout.strip()
            except:
                pass
        
        if not self.api_key or not self.api_secret:
            print(f"{Colors.FAIL}❌ Error: DataForSEO credentials not found!{Colors.ENDC}")
            print(f"{Colors.WARNING}Please set DATAFORSEO_API_KEY and DATAFORSEO_API_SECRET environment variables.{Colors.ENDC}")
            sys.exit(1)
        
        # Strip whitespace
        self.api_key = self.api_key.strip()
        self.api_secret = self.api_secret.strip()
        
        # Create Basic Auth header
        credentials = f"{self.api_key}:{self.api_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.auth_header = f"Basic {encoded_credentials}"
        
        print(f"{Colors.OKGREEN}✓ DataForSEO credentials loaded{Colors.ENDC}")
    
    async def _make_request(self, endpoint: str, payload: list, timeout: int = 120) -> Dict[str, Any]:
        """Make a request to DataForSEO API."""
        url = f"{self.BASE_URL}/{endpoint}"
        headers = {
            "Authorization": self.auth_header,
            "Content-Type": "application/json"
        }
        
        print(f"\n{Colors.OKCYAN}📡 Requesting: {endpoint}{Colors.ENDC}")
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                print(f"{Colors.FAIL}❌ HTTP Error {e.response.status_code}: {e.response.text[:200]}{Colors.ENDC}")
                raise
            except Exception as e:
                print(f"{Colors.FAIL}❌ Request failed: {e}{Colors.ENDC}")
                raise
    
    async def generate_subtopics(self, text: str, max_subtopics: int = 5) -> Dict[str, Any]:
        """Generate subtopics from text."""
        payload = [{
            "text": text,
            "max_subtopics": max_subtopics,
            "language": "en"
        }]
        
        response = await self._make_request("content_generation/generate_subtopics/live", payload)
        
        if response.get("tasks") and len(response["tasks"]) > 0:
            task = response["tasks"][0]
            if task.get("status_code") == 20000 and task.get("result"):
                result_item = task["result"][0]
                return {
                    "success": True,
                    "subtopics": result_item.get("subtopics", []),
                    "count": len(result_item.get("subtopics", []))
                }
            else:
                return {
                    "success": False,
                    "error": f"{task.get('status_code')}: {task.get('status_message', 'Unknown error')}"
                }
        return {"success": False, "error": "Invalid response"}
    
    async def generate_text(self, prompt: str, max_tokens: int = 200) -> Dict[str, Any]:
        """Generate text content."""
        payload = [{
            "text": prompt,
            "max_tokens": max_tokens,
            "temperature": 0.7
        }]
        
        response = await self._make_request("content_generation/generate_text/live", payload)
        
        if response.get("tasks") and len(response["tasks"]) > 0:
            task = response["tasks"][0]
            if task.get("status_code") == 20000 and task.get("result"):
                result_item = task["result"][0]
                return {
                    "success": True,
                    "text": result_item.get("text", ""),
                    "tokens_used": result_item.get("tokens_used", 0)
                }
            else:
                return {
                    "success": False,
                    "error": f"{task.get('status_code')}: {task.get('status_message', 'Unknown error')}"
                }
        return {"success": False, "error": "Invalid response"}
    
    async def generate_meta_tags(self, title: str, content: str) -> Dict[str, Any]:
        """Generate meta tags."""
        payload = [{
            "title": title,
            "text": content,
            "language": "en"
        }]
        
        response = await self._make_request("content_generation/generate_meta_tags/live", payload)
        
        if response.get("tasks") and len(response["tasks"]) > 0:
            task = response["tasks"][0]
            if task.get("status_code") == 20000 and task.get("result"):
                result_item = task["result"][0]
                return {
                    "success": True,
                    "meta_title": result_item.get("title", title),
                    "meta_description": result_item.get("description", ""),
                    "summary": result_item.get("summary", ""),
                    "keywords": result_item.get("keywords", [])
                }
            else:
                return {
                    "success": False,
                    "error": f"{task.get('status_code')}: {task.get('status_message', 'Unknown error')}"
                }
        return {"success": False, "error": "Invalid response"}


async def main():
    """Main test function."""
    print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}DataForSEO Content Generation - 100 Word Blog Test{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")
    
    tester = DataForSEOTester()
    
    # Test parameters
    topic = "Benefits of Python Programming"
    keywords = ["Python", "programming", "coding", "development"]
    word_count = 100
    
    print(f"{Colors.BOLD}Test Parameters:{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Topic: {topic}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Keywords: {', '.join(keywords)}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Target Word Count: {word_count} words{Colors.ENDC}\n")
    
    # Step 1: Generate subtopics
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}STEP 1: Generate Subtopics from Main Topic{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")
    
    subtopic_prompt = f"Topic: {topic}. Keywords: {', '.join(keywords)}"
    print(f"{Colors.OKCYAN}Prompt: {subtopic_prompt}{Colors.ENDC}\n")
    
    subtopics_result = await tester.generate_subtopics(subtopic_prompt, max_subtopics=5)
    
    if subtopics_result.get("success"):
        subtopics = subtopics_result.get("subtopics", [])
        print(f"{Colors.OKGREEN}✓ Subtopics Generated: {len(subtopics)}{Colors.ENDC}")
        for i, subtopic in enumerate(subtopics, 1):
            print(f"{Colors.OKBLUE}{i}. {subtopic}{Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}⚠ Subtopics generation failed: {subtopics_result.get('error')}{Colors.ENDC}")
        subtopics = []
    
    # Step 2: Generate 100-word content
    print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}STEP 2: Generate 100-Word Blog Content{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")
    
    # Build content prompt
    content_prompt = f"""Write a concise blog post about {topic}.

Keywords to include: {', '.join(keywords)}
Target word count: exactly {word_count} words
Tone: professional and engaging
Structure: Brief introduction, main points, and short conclusion

"""
    
    if subtopics:
        content_prompt += f"Cover these subtopics:\n"
        for subtopic in subtopics[:3]:
            content_prompt += f"- {subtopic}\n"
    
    print(f"{Colors.OKCYAN}Generating content...{Colors.ENDC}\n")
    
    # Estimate tokens: 100 words ≈ 133 tokens, add buffer for prompt
    max_tokens = 200
    
    content_result = await tester.generate_text(content_prompt, max_tokens=max_tokens)
    
    if content_result.get("success"):
        generated_text = content_result.get("text", "")
        tokens_used = content_result.get("tokens_used", 0)
        actual_word_count = len(generated_text.split())
        
        print(f"{Colors.OKGREEN}✓ Content Generated!{Colors.ENDC}")
        print(f"{Colors.OKCYAN}Tokens Used: {tokens_used}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}Word Count: {actual_word_count} words{Colors.ENDC}")
        print(f"\n{Colors.BOLD}Generated Content:{Colors.ENDC}")
        print(f"{Colors.OKBLUE}{generated_text}{Colors.ENDC}\n")
    else:
        print(f"{Colors.FAIL}❌ Content generation failed: {content_result.get('error')}{Colors.ENDC}")
        generated_text = ""
        tokens_used = 0
        actual_word_count = 0
    
    # Step 3: Generate meta tags
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}STEP 3: Generate Meta Tags{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")
    
    if generated_text:
        meta_result = await tester.generate_meta_tags(topic, generated_text[:1000])
        
        if meta_result.get("success"):
            print(f"{Colors.OKGREEN}✓ Meta Tags Generated!{Colors.ENDC}")
            print(f"\n{Colors.BOLD}Meta Title:{Colors.ENDC}")
            print(f"{Colors.OKBLUE}{meta_result.get('meta_title', topic)}{Colors.ENDC}")
            print(f"\n{Colors.BOLD}Meta Description:{Colors.ENDC}")
            print(f"{Colors.OKBLUE}{meta_result.get('meta_description', '')}{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}⚠ Meta tags generation failed: {meta_result.get('error')}{Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}⚠ Skipping meta tags (no content generated){Colors.ENDC}")
    
    # Summary
    print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}SUMMARY{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")
    
    print(f"{Colors.BOLD}Results:{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Topic: {topic}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Subtopics: {len(subtopics)}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Content: {actual_word_count} words (target: {word_count}){Colors.ENDC}")
    
    if actual_word_count > 0:
        diff = abs(actual_word_count - word_count)
        diff_percent = (diff / word_count) * 100
        if diff_percent <= 25:
            print(f"{Colors.OKGREEN}✓ Word count within acceptable range ({diff_percent:.1f}% difference){Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}⚠ Word count differs by {diff_percent:.1f}%{Colors.ENDC}")
    
    # Cost estimate
    subtopics_cost = 0.0001
    content_cost = tokens_used * 0.00005
    meta_cost = 0.001
    total_cost = subtopics_cost + content_cost + meta_cost
    
    print(f"\n{Colors.BOLD}Estimated Cost:{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Subtopics: ${subtopics_cost:.5f}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Content: ${content_cost:.5f}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Meta Tags: ${meta_cost:.5f}{Colors.ENDC}")
    print(f"{Colors.BOLD}Total: ${total_cost:.5f}{Colors.ENDC}")
    
    print(f"\n{Colors.OKGREEN}{'='*80}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}Test completed!{Colors.ENDC}")
    print(f"{Colors.OKGREEN}{'='*80}{Colors.ENDC}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Test interrupted{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.FAIL}Test failed: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

