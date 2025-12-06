#!/usr/bin/env python3
"""
Direct test script for DataForSEO Content Generation API.

This script tests the DataForSEO Content Generation API endpoints directly:
- Generate Text
- Generate Subtopics  
- Generate Meta Tags

Usage:
    python test_dataforseo_content_generation_direct.py

Environment Variables Required:
    DATAFORSEO_API_KEY - Your DataForSEO API key (username)
    DATAFORSEO_API_SECRET - Your DataForSEO API secret (password)
"""

import os
import sys
import asyncio
import httpx
import base64
import json
from typing import Dict, Any, Optional
from datetime import datetime

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
    UNDERLINE = '\033[4m'


class DataForSEOContentGenerationTester:
    """Test client for DataForSEO Content Generation API."""
    
    BASE_URL = "https://api.dataforseo.com/v3"
    
    def __init__(self):
        """Initialize the tester with credentials from environment."""
        self.api_key = os.getenv("DATAFORSEO_API_KEY") or os.getenv("DATAFORSEO_API_LOGIN")
        self.api_secret = os.getenv("DATAFORSEO_API_SECRET") or os.getenv("DATAFORSEO_API_PASSWORD")
        
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
        print(f"{Colors.OKCYAN}API Key: {self.api_key[:10]}...{self.api_key[-4:]}{Colors.ENDC}")
    
    async def _make_request(
        self,
        endpoint: str,
        payload: list,
        timeout: int = 120
    ) -> Dict[str, Any]:
        """
        Make a request to DataForSEO API.
        
        Args:
            endpoint: API endpoint path (e.g., "content_generation/generate_text/live")
            payload: Request payload as a list
            timeout: Request timeout in seconds
            
        Returns:
            API response as dictionary
        """
        url = f"{self.BASE_URL}/{endpoint}"
        headers = {
            "Authorization": self.auth_header,
            "Content-Type": "application/json"
        }
        
        print(f"\n{Colors.OKBLUE}📡 Making request to: {endpoint}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}Payload: {json.dumps(payload, indent=2)}{Colors.ENDC}")
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                result = response.json()
                print(f"{Colors.OKGREEN}✓ Request successful (Status: {response.status_code}){Colors.ENDC}")
                return result
                
            except httpx.HTTPStatusError as e:
                print(f"{Colors.FAIL}❌ HTTP Error: {e.response.status_code}{Colors.ENDC}")
                print(f"{Colors.FAIL}Response: {e.response.text}{Colors.ENDC}")
                raise
            except Exception as e:
                print(f"{Colors.FAIL}❌ Request failed: {e}{Colors.ENDC}")
                raise
    
    async def test_generate_text(
        self,
        prompt: str = "Write a short blog post about the benefits of Python programming.",
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Test the generate_text endpoint.
        
        Args:
            prompt: Text prompt for generation
            max_tokens: Maximum tokens to generate
            temperature: Creativity level (0.0-1.0)
            
        Returns:
            Generated text result
        """
        print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}TEST 1: Generate Text{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")
        
        payload = [{
            "text": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        }]
        
        try:
            response = await self._make_request("content_generation/generate_text/live", payload)
            
            # Parse response
            if response.get("tasks") and len(response["tasks"]) > 0:
                task = response["tasks"][0]
                
                if task.get("status_code") == 20000:
                    if task.get("result") and len(task["result"]) > 0:
                        result_item = task["result"][0]
                        generated_text = result_item.get("text", "")
                        tokens_used = result_item.get("tokens_used", 0)
                        
                        print(f"\n{Colors.OKGREEN}✓ Text Generated Successfully!{Colors.ENDC}")
                        print(f"{Colors.OKCYAN}Tokens Used: {tokens_used}{Colors.ENDC}")
                        print(f"{Colors.OKCYAN}Text Length: {len(generated_text)} characters{Colors.ENDC}")
                        print(f"\n{Colors.BOLD}Generated Text:{Colors.ENDC}")
                        print(f"{Colors.OKBLUE}{generated_text}{Colors.ENDC}")
                        
                        return {
                            "success": True,
                            "text": generated_text,
                            "tokens_used": tokens_used,
                            "metadata": result_item.get("metadata", {})
                        }
                    else:
                        print(f"{Colors.WARNING}⚠ No result in response{Colors.ENDC}")
                        print(f"Task: {json.dumps(task, indent=2)}")
                        return {"success": False, "error": "No result in response"}
                else:
                    status_code = task.get("status_code")
                    status_message = task.get("status_message", "Unknown error")
                    print(f"{Colors.FAIL}❌ API Error: {status_code} - {status_message}{Colors.ENDC}")
                    return {"success": False, "error": f"{status_code}: {status_message}"}
            else:
                print(f"{Colors.FAIL}❌ Invalid response structure{Colors.ENDC}")
                print(f"Response: {json.dumps(response, indent=2)}")
                return {"success": False, "error": "Invalid response structure"}
                
        except Exception as e:
            print(f"{Colors.FAIL}❌ Test failed: {e}{Colors.ENDC}")
            return {"success": False, "error": str(e)}
    
    async def test_generate_subtopics(
        self,
        text: str = "Python programming language is widely used for web development, data science, and automation.",
        max_subtopics: int = 5,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Test the generate_subtopics endpoint.
        
        Args:
            text: Input text to generate subtopics from
            max_subtopics: Maximum number of subtopics
            language: Language code
            
        Returns:
            Generated subtopics result
        """
        print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}TEST 2: Generate Subtopics{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")
        
        payload = [{
            "text": text,
            "max_subtopics": max_subtopics,
            "language": language
        }]
        
        try:
            response = await self._make_request("content_generation/generate_subtopics/live", payload)
            
            # Parse response
            if response.get("tasks") and len(response["tasks"]) > 0:
                task = response["tasks"][0]
                
                if task.get("status_code") == 20000:
                    if task.get("result") and len(task["result"]) > 0:
                        result_item = task["result"][0]
                        subtopics = result_item.get("subtopics", [])
                        
                        print(f"\n{Colors.OKGREEN}✓ Subtopics Generated Successfully!{Colors.ENDC}")
                        print(f"{Colors.OKCYAN}Number of Subtopics: {len(subtopics)}{Colors.ENDC}")
                        print(f"\n{Colors.BOLD}Generated Subtopics:{Colors.ENDC}")
                        for i, subtopic in enumerate(subtopics, 1):
                            print(f"{Colors.OKBLUE}{i}. {subtopic}{Colors.ENDC}")
                        
                        return {
                            "success": True,
                            "subtopics": subtopics,
                            "count": len(subtopics),
                            "metadata": result_item.get("metadata", {})
                        }
                    else:
                        print(f"{Colors.WARNING}⚠ No result in response{Colors.ENDC}")
                        print(f"Task: {json.dumps(task, indent=2)}")
                        return {"success": False, "error": "No result in response"}
                else:
                    status_code = task.get("status_code")
                    status_message = task.get("status_message", "Unknown error")
                    print(f"{Colors.FAIL}❌ API Error: {status_code} - {status_message}{Colors.ENDC}")
                    return {"success": False, "error": f"{status_code}: {status_message}"}
            else:
                print(f"{Colors.FAIL}❌ Invalid response structure{Colors.ENDC}")
                print(f"Response: {json.dumps(response, indent=2)}")
                return {"success": False, "error": "Invalid response structure"}
                
        except Exception as e:
            print(f"{Colors.FAIL}❌ Test failed: {e}{Colors.ENDC}")
            return {"success": False, "error": str(e)}
    
    async def test_generate_meta_tags(
        self,
        title: str = "Python Programming: A Comprehensive Guide",
        content: str = "Python is a versatile programming language used for web development, data science, machine learning, and automation. It offers simplicity, readability, and a vast ecosystem of libraries.",
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Test the generate_meta_tags endpoint.
        
        Args:
            title: Page title
            content: Page content
            language: Language code
            
        Returns:
            Generated meta tags result
        """
        print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}TEST 3: Generate Meta Tags{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")
        
        payload = [{
            "title": title,
            "text": content,
            "language": language
        }]
        
        try:
            response = await self._make_request("content_generation/generate_meta_tags/live", payload)
            
            # Parse response
            if response.get("tasks") and len(response["tasks"]) > 0:
                task = response["tasks"][0]
                
                if task.get("status_code") == 20000:
                    if task.get("result") and len(task["result"]) > 0:
                        result_item = task["result"][0]
                        meta_title = result_item.get("title", title)
                        meta_description = result_item.get("description", "")
                        summary = result_item.get("summary", "")
                        keywords = result_item.get("keywords", [])
                        
                        print(f"\n{Colors.OKGREEN}✓ Meta Tags Generated Successfully!{Colors.ENDC}")
                        print(f"\n{Colors.BOLD}Meta Title:{Colors.ENDC}")
                        print(f"{Colors.OKBLUE}{meta_title}{Colors.ENDC}")
                        print(f"\n{Colors.BOLD}Meta Description:{Colors.ENDC}")
                        print(f"{Colors.OKBLUE}{meta_description}{Colors.ENDC}")
                        if summary:
                            print(f"\n{Colors.BOLD}Summary:{Colors.ENDC}")
                            print(f"{Colors.OKBLUE}{summary}{Colors.ENDC}")
                        if keywords:
                            print(f"\n{Colors.BOLD}Keywords:{Colors.ENDC}")
                            print(f"{Colors.OKBLUE}{', '.join(keywords)}{Colors.ENDC}")
                        
                        return {
                            "success": True,
                            "meta_title": meta_title,
                            "meta_description": meta_description,
                            "summary": summary,
                            "keywords": keywords,
                            "metadata": result_item.get("metadata", {})
                        }
                    else:
                        print(f"{Colors.WARNING}⚠ No result in response{Colors.ENDC}")
                        print(f"Task: {json.dumps(task, indent=2)}")
                        return {"success": False, "error": "No result in response"}
                else:
                    status_code = task.get("status_code")
                    status_message = task.get("status_message", "Unknown error")
                    print(f"{Colors.FAIL}❌ API Error: {status_code} - {status_message}{Colors.ENDC}")
                    return {"success": False, "error": f"{status_code}: {status_message}"}
            else:
                print(f"{Colors.FAIL}❌ Invalid response structure{Colors.ENDC}")
                print(f"Response: {json.dumps(response, indent=2)}")
                return {"success": False, "error": "Invalid response structure"}
                
        except Exception as e:
            print(f"{Colors.FAIL}❌ Test failed: {e}{Colors.ENDC}")
            return {"success": False, "error": str(e)}
    
    async def test_complete_blog_generation(
        self,
        topic: str = "Python Programming Benefits",
        keywords: list = ["Python", "programming", "web development"],
        word_count: int = 500
    ) -> Dict[str, Any]:
        """
        Test complete blog generation workflow:
        1. Generate subtopics
        2. Generate main content
        3. Generate meta tags
        
        Args:
            topic: Blog topic
            keywords: List of keywords
            word_count: Target word count
            
        Returns:
            Complete blog generation result
        """
        print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}TEST 4: Complete Blog Generation Workflow{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")
        
        results = {
            "topic": topic,
            "keywords": keywords,
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
        
        # Step 1: Generate subtopics
        print(f"\n{Colors.BOLD}Step 1: Generating subtopics...{Colors.ENDC}")
        subtopic_prompt = f"Topic: {topic}. Keywords: {', '.join(keywords)}"
        subtopics_result = await self.test_generate_subtopics(
            text=subtopic_prompt,
            max_subtopics=5
        )
        results["tests"]["subtopics"] = subtopics_result
        
        if not subtopics_result.get("success"):
            print(f"{Colors.WARNING}⚠ Subtopics generation failed, continuing anyway...{Colors.ENDC}")
        
        # Step 2: Generate main content
        print(f"\n{Colors.BOLD}Step 2: Generating main content...{Colors.ENDC}")
        content_prompt = f"""Write a comprehensive blog post about {topic}.

Keywords to include: {', '.join(keywords)}
Target word count: approximately {word_count} words
Tone: professional
Structure: Include introduction, main content sections, and conclusion"""
        
        # Estimate tokens (roughly 1 token = 0.75 words)
        estimated_tokens = int(word_count / 0.75)
        max_tokens = min(estimated_tokens + 200, 2000)  # Add buffer, cap at 2000
        
        content_result = await self.test_generate_text(
            prompt=content_prompt,
            max_tokens=max_tokens,
            temperature=0.7
        )
        results["tests"]["content"] = content_result
        
        if not content_result.get("success"):
            print(f"{Colors.FAIL}❌ Content generation failed!{Colors.ENDC}")
            return results
        
        # Step 3: Generate meta tags
        print(f"\n{Colors.BOLD}Step 3: Generating meta tags...{Colors.ENDC}")
        generated_content = content_result.get("text", "")
        meta_title = topic
        
        meta_result = await self.test_generate_meta_tags(
            title=meta_title,
            content=generated_content[:2000]  # Limit content length for meta generation
        )
        results["tests"]["meta_tags"] = meta_result
        
        # Summary
        print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}COMPLETE BLOG GENERATION SUMMARY{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")
        
        all_success = all(
            result.get("success", False) 
            for result in results["tests"].values()
        )
        
        if all_success:
            print(f"{Colors.OKGREEN}✓ All steps completed successfully!{Colors.ENDC}")
            
            # Calculate costs
            subtopics_cost = 0.0001  # $0.0001 per task
            content_cost = content_result.get("tokens_used", 0) * 0.00005  # $0.00005 per token
            meta_cost = 0.001  # $0.001 per task
            total_cost = subtopics_cost + content_cost + meta_cost
            
            print(f"\n{Colors.BOLD}Cost Breakdown:{Colors.ENDC}")
            print(f"{Colors.OKCYAN}Subtopics: ${subtopics_cost:.5f}{Colors.ENDC}")
            print(f"{Colors.OKCYAN}Content ({content_result.get('tokens_used', 0)} tokens): ${content_cost:.5f}{Colors.ENDC}")
            print(f"{Colors.OKCYAN}Meta Tags: ${meta_cost:.5f}{Colors.ENDC}")
            print(f"{Colors.BOLD}Total Cost: ${total_cost:.5f}{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}⚠ Some steps failed. Check individual test results above.{Colors.ENDC}")
        
        return results


async def main():
    """Main test function."""
    print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}DataForSEO Content Generation API - Direct Test{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")
    
    tester = DataForSEOContentGenerationTester()
    
    # Run individual tests
    print(f"\n{Colors.BOLD}Running individual endpoint tests...{Colors.ENDC}")
    
    # Test 1: Generate Text
    await tester.test_generate_text(
        prompt="Write a short paragraph about the benefits of using Python for data science.",
        max_tokens=300,
        temperature=0.7
    )
    
    # Test 2: Generate Subtopics
    await tester.test_generate_subtopics(
        text="Python is a versatile programming language used for web development, data science, machine learning, automation, and scientific computing.",
        max_subtopics=5
    )
    
    # Test 3: Generate Meta Tags
    await tester.test_generate_meta_tags(
        title="Python Programming Guide",
        content="Python is a high-level programming language known for its simplicity and readability. It's widely used in web development, data science, machine learning, and automation."
    )
    
    # Test 4: Complete Blog Generation Workflow
    await tester.test_complete_blog_generation(
        topic="Benefits of Python Programming",
        keywords=["Python", "programming", "web development", "data science"],
        word_count=500
    )
    
    print(f"\n{Colors.OKGREEN}{'='*80}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}All tests completed!{Colors.ENDC}")
    print(f"{Colors.OKGREEN}{'='*80}{Colors.ENDC}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Test interrupted by user{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.FAIL}Test failed with error: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

