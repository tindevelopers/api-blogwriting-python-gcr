#!/usr/bin/env python3
"""
Test DataForSEO Content Generation for 100-word blog with main topic and subtopics.

This script tests:
1. Generate subtopics from a main topic
2. Generate 100-word blog content
3. Generate meta tags

Usage:
    python3 test_100_words_blog.py
"""

import asyncio
import os
import sys
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.blog_writer_sdk.services.dataforseo_content_generation_service import (
    DataForSEOContentGenerationService,
    BlogType
)
from src.blog_writer_sdk.integrations.dataforseo_integration import DataForSEOClient

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


async def test_100_word_blog():
    """Test generating a 100-word blog with subtopics."""
    
    print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}DataForSEO Content Generation - 100 Word Blog Test{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")
    
    # Initialize DataForSEO client
    print(f"{Colors.OKCYAN}Initializing DataForSEO client...{Colors.ENDC}")
    client = DataForSEOClient()
    await client.initialize_credentials("default")
    
    if not client.is_configured:
        print(f"{Colors.FAIL}❌ DataForSEO credentials not configured!{Colors.ENDC}")
        print(f"{Colors.WARNING}Please set DATAFORSEO_API_KEY and DATAFORSEO_API_SECRET environment variables.{Colors.ENDC}")
        print(f"{Colors.WARNING}Or ensure credentials are available in Google Secret Manager.{Colors.ENDC}")
        return
    
    print(f"{Colors.OKGREEN}✓ DataForSEO client initialized{Colors.ENDC}\n")
    
    # Initialize service
    print(f"{Colors.OKCYAN}Initializing Content Generation Service...{Colors.ENDC}")
    service = DataForSEOContentGenerationService(dataforseo_client=client)
    await service.initialize("default")
    
    if not service.is_configured:
        print(f"{Colors.FAIL}❌ Service not configured!{Colors.ENDC}")
        return
    
    print(f"{Colors.OKGREEN}✓ Service initialized{Colors.ENDC}\n")
    
    # Test parameters
    topic = "Benefits of Python Programming"
    keywords = ["Python", "programming", "coding", "development"]
    word_count = 100
    
    print(f"{Colors.BOLD}Test Parameters:{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Topic: {topic}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Keywords: {', '.join(keywords)}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Target Word Count: {word_count} words{Colors.ENDC}\n")
    
    # Step 1: Generate subtopics from main topic
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}STEP 1: Generate Subtopics from Main Topic{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")
    
    subtopic_prompt = f"Topic: {topic}. Keywords: {', '.join(keywords)}"
    print(f"{Colors.OKCYAN}Prompt: {subtopic_prompt}{Colors.ENDC}\n")
    
    try:
        subtopics_result = await service.generate_subtopics(
            text=subtopic_prompt,
            max_subtopics=5,
            language="en",
            tenant_id="default"
        )
        
        subtopics = subtopics_result.get("subtopics", [])
        subtopics_cost = subtopics_result.get("cost", 0.0)
        
        if subtopics:
            print(f"{Colors.OKGREEN}✓ Subtopics Generated Successfully!{Colors.ENDC}")
            print(f"{Colors.OKCYAN}Number of Subtopics: {len(subtopics)}{Colors.ENDC}")
            print(f"{Colors.OKCYAN}Cost: ${subtopics_cost:.5f}{Colors.ENDC}")
            print(f"\n{Colors.BOLD}Generated Subtopics:{Colors.ENDC}")
            for i, subtopic in enumerate(subtopics, 1):
                print(f"{Colors.OKBLUE}{i}. {subtopic}{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}⚠ No subtopics generated{Colors.ENDC}")
            subtopics = []
            
    except Exception as e:
        print(f"{Colors.FAIL}❌ Subtopics generation failed: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        subtopics = []
    
    # Step 2: Generate 100-word blog content
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
    
    # Add subtopics to prompt if available
    if subtopics:
        content_prompt += f"Subtopics to cover:\n"
        for subtopic in subtopics[:3]:  # Use top 3 subtopics
            content_prompt += f"- {subtopic}\n"
    
    print(f"{Colors.OKCYAN}Content Prompt:{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{content_prompt[:200]}...{Colors.ENDC}\n")
    
    try:
        # Estimate tokens (roughly 1 token = 0.75 words)
        # For 100 words, we need ~133 tokens, but add buffer for prompt
        estimated_tokens = int(word_count / 0.75) + 100  # Add buffer for prompt
        max_tokens = min(estimated_tokens, 500)  # Cap at 500 for short content
        
        print(f"{Colors.OKCYAN}Generating content (max_tokens: {max_tokens})...{Colors.ENDC}\n")
        
        content_result = await service.generate_text(
            prompt=content_prompt,
            max_tokens=max_tokens,
            temperature=0.7,
            tone="professional",
            language="en",
            tenant_id="default"
        )
        
        generated_text = content_result.get("text", "")
        tokens_used = content_result.get("tokens_used", 0)
        content_cost = content_result.get("cost", 0.0)
        actual_word_count = len(generated_text.split())
        
        if generated_text:
            print(f"{Colors.OKGREEN}✓ Content Generated Successfully!{Colors.ENDC}")
            print(f"{Colors.OKCYAN}Tokens Used: {tokens_used}{Colors.ENDC}")
            print(f"{Colors.OKCYAN}Word Count: {actual_word_count} words{Colors.ENDC}")
            print(f"{Colors.OKCYAN}Cost: ${content_cost:.5f}{Colors.ENDC}")
            print(f"\n{Colors.BOLD}Generated Content:{Colors.ENDC}")
            print(f"{Colors.OKBLUE}{generated_text}{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}❌ No content generated{Colors.ENDC}")
            generated_text = ""
            
    except Exception as e:
        print(f"{Colors.FAIL}❌ Content generation failed: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        generated_text = ""
        tokens_used = 0
        content_cost = 0.0
        actual_word_count = 0
    
    # Step 3: Generate meta tags
    print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}STEP 3: Generate Meta Tags{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")
    
    if not generated_text:
        print(f"{Colors.WARNING}⚠ Skipping meta tags generation (no content generated){Colors.ENDC}")
        meta_title = topic
        meta_description = ""
        meta_cost = 0.0
    else:
        try:
            meta_title = topic
            meta_content = generated_text[:1000]  # Limit content for meta generation
            
            print(f"{Colors.OKCYAN}Generating meta tags...{Colors.ENDC}\n")
            
            meta_result = await service.generate_meta_tags(
                title=meta_title,
                content=meta_content,
                language="en",
                tenant_id="default"
            )
            
            meta_title = meta_result.get("meta_title", topic)
            meta_description = meta_result.get("meta_description", "")
            meta_cost = meta_result.get("cost", 0.0)
            
            if meta_description:
                print(f"{Colors.OKGREEN}✓ Meta Tags Generated Successfully!{Colors.ENDC}")
                print(f"{Colors.OKCYAN}Cost: ${meta_cost:.5f}{Colors.ENDC}")
                print(f"\n{Colors.BOLD}Meta Title:{Colors.ENDC}")
                print(f"{Colors.OKBLUE}{meta_title}{Colors.ENDC}")
                print(f"\n{Colors.BOLD}Meta Description:{Colors.ENDC}")
                print(f"{Colors.OKBLUE}{meta_description}{Colors.ENDC}")
            else:
                print(f"{Colors.WARNING}⚠ No meta description generated{Colors.ENDC}")
                meta_cost = 0.0
                
        except Exception as e:
            print(f"{Colors.FAIL}❌ Meta tags generation failed: {e}{Colors.ENDC}")
            import traceback
            traceback.print_exc()
            meta_title = topic
            meta_description = ""
            meta_cost = 0.0
    
    # Summary
    print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}TEST SUMMARY{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")
    
    total_cost = subtopics_cost + content_cost + meta_cost
    
    print(f"{Colors.BOLD}Results:{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Topic: {topic}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Subtopics Generated: {len(subtopics)}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Content Word Count: {actual_word_count} words (target: {word_count}){Colors.ENDC}")
    print(f"{Colors.OKCYAN}Meta Tags: {'✓' if meta_description else '✗'}{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}Cost Breakdown:{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Subtopics: ${subtopics_cost:.5f}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Content ({tokens_used} tokens): ${content_cost:.5f}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Meta Tags: ${meta_cost:.5f}{Colors.ENDC}")
    print(f"{Colors.BOLD}Total Cost: ${total_cost:.5f}{Colors.ENDC}")
    
    # Word count check
    if actual_word_count > 0:
        word_diff = abs(actual_word_count - word_count)
        word_diff_percent = (word_diff / word_count) * 100
        
        if word_diff_percent <= 25:  # Within 25% tolerance
            print(f"\n{Colors.OKGREEN}✓ Word count within acceptable range ({word_diff_percent:.1f}% difference){Colors.ENDC}")
        else:
            print(f"\n{Colors.WARNING}⚠ Word count differs by {word_diff_percent:.1f}% from target{Colors.ENDC}")
    
    print(f"\n{Colors.OKGREEN}{'='*80}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}Test completed!{Colors.ENDC}")
    print(f"{Colors.OKGREEN}{'='*80}{Colors.ENDC}\n")
    
    return {
        "topic": topic,
        "subtopics": subtopics,
        "content": generated_text,
        "word_count": actual_word_count,
        "target_word_count": word_count,
        "meta_title": meta_title,
        "meta_description": meta_description,
        "cost": total_cost,
        "tokens_used": tokens_used
    }


if __name__ == "__main__":
    try:
        result = asyncio.run(test_100_word_blog())
        if result.get("content"):
            print(f"\n{Colors.BOLD}Final Blog Content:{Colors.ENDC}")
            print(f"{Colors.OKBLUE}{result['content']}{Colors.ENDC}\n")
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Test interrupted by user{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.FAIL}Test failed with error: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

