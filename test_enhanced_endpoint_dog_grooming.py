#!/usr/bin/env python3
"""
Test the /api/v1/blog/generate-enhanced endpoint with new DataForSEO format.
Tests a 100-word blog about dog grooming.
"""

import asyncio
import httpx
import json
import os
from datetime import datetime

# Colors for output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


async def test_enhanced_endpoint():
    """Test the enhanced blog generation endpoint."""
    
    print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}Testing /api/v1/blog/generate-enhanced - Dog Grooming Blog{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")
    
    # Determine API URL
    api_url = os.getenv("API_URL", "http://localhost:8000")
    endpoint = f"{api_url}/api/v1/blog/generate-enhanced"
    
    print(f"{Colors.OKCYAN}API Endpoint: {endpoint}{Colors.ENDC}\n")
    
    # Request payload for 100-word blog about dog grooming
    payload = {
        "topic": "Dog Grooming Tips for Pet Owners",
        "keywords": [
            "dog grooming",
            "pet grooming",
            "dog care",
            "grooming tips",
            "pet hygiene"
        ],
        "tone": "professional",
        "length": "short",  # short = 500 words, but we'll override with word_count_target
        "word_count_target": 100,  # Target 100 words
        "blog_type": "guide",  # Use guide type
        "use_dataforseo_content_generation": True,  # Use DataForSEO API
        "optimize_for_traffic": True,
        "target_audience": "pet owners and dog enthusiasts"
    }
    
    print(f"{Colors.BOLD}Request Payload:{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{json.dumps(payload, indent=2)}{Colors.ENDC}\n")
    
    print(f"{Colors.OKCYAN}📡 Sending request to endpoint...{Colors.ENDC}\n")
    
    start_time = datetime.now()
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                endpoint,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            elapsed_time = (datetime.now() - start_time).total_seconds()
            
            print(f"{Colors.OKCYAN}Response Status: {response.status_code}{Colors.ENDC}")
            print(f"{Colors.OKCYAN}Response Time: {elapsed_time:.2f} seconds{Colors.ENDC}\n")
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"{Colors.OKGREEN}✓ Blog Generated Successfully!{Colors.ENDC}\n")
                
                # Extract key information
                title = result.get("title", "N/A")
                content = result.get("content", "")
                meta_title = result.get("meta_title", "")
                meta_description = result.get("meta_description", "")
                word_count = len(content.split()) if content else 0
                
                # Quality metrics
                readability_score = result.get("readability_score", 0)
                seo_score = result.get("seo_score", 0)
                
                # Cost and tokens
                total_tokens = result.get("total_tokens", 0)
                total_cost = result.get("total_cost", 0)
                generation_time = result.get("generation_time", 0)
                
                # Subtopics (if available)
                subtopics = result.get("subtopics", [])
                
                print(f"{Colors.BOLD}Generated Blog:{Colors.ENDC}")
                print(f"{Colors.OKBLUE}{'='*80}{Colors.ENDC}")
                print(f"{Colors.BOLD}Title:{Colors.ENDC} {title}")
                print(f"{Colors.BOLD}Word Count:{Colors.ENDC} {word_count} words (target: 100)")
                print(f"{Colors.BOLD}Readability Score:{Colors.ENDC} {readability_score:.1f}/100")
                print(f"{Colors.BOLD}SEO Score:{Colors.ENDC} {seo_score:.1f}/100")
                print(f"{Colors.OKBLUE}{'='*80}{Colors.ENDC}\n")
                
                print(f"{Colors.BOLD}Meta Title:{Colors.ENDC}")
                print(f"{Colors.OKBLUE}{meta_title}{Colors.ENDC}\n")
                
                print(f"{Colors.BOLD}Meta Description:{Colors.ENDC}")
                print(f"{Colors.OKBLUE}{meta_description}{Colors.ENDC}\n")
                
                if subtopics:
                    print(f"{Colors.BOLD}Subtopics Generated ({len(subtopics)}):{Colors.ENDC}")
                    for i, subtopic in enumerate(subtopics[:10], 1):
                        print(f"{Colors.OKCYAN}{i}. {subtopic}{Colors.ENDC}")
                    print()
                
                print(f"{Colors.BOLD}Blog Content:{Colors.ENDC}")
                print(f"{Colors.OKBLUE}{content}{Colors.ENDC}\n")
                
                print(f"{Colors.BOLD}Performance Metrics:{Colors.ENDC}")
                print(f"{Colors.OKCYAN}Total Tokens: {total_tokens}{Colors.ENDC}")
                print(f"{Colors.OKCYAN}Total Cost: ${total_cost:.5f}{Colors.ENDC}")
                print(f"{Colors.OKCYAN}Generation Time: {generation_time:.2f} seconds{Colors.ENDC}\n")
                
                # Word count check
                if word_count > 0:
                    diff = abs(word_count - 100)
                    diff_percent = (diff / 100) * 100
                    if diff_percent <= 25:
                        print(f"{Colors.OKGREEN}✓ Word count within acceptable range ({diff_percent:.1f}% difference){Colors.ENDC}")
                    else:
                        print(f"{Colors.WARNING}⚠ Word count differs by {diff_percent:.1f}% from target{Colors.ENDC}")
                
                # Save to file
                output_file = "generated_blog_dog_grooming.md"
                with open(output_file, "w") as f:
                    f.write(f"# {title}\n\n")
                    f.write(f"**Meta Description:** {meta_description}\n\n")
                    f.write("---\n\n")
                    f.write(f"{content}\n\n")
                    f.write("---\n\n")
                    if subtopics:
                        f.write("## Related Subtopics\n\n")
                        for i, subtopic in enumerate(subtopics, 1):
                            f.write(f"{i}. {subtopic}\n")
                        f.write("\n---\n\n")
                    f.write("## Blog Details\n\n")
                    f.write(f"- **Topic:** Dog Grooming Tips for Pet Owners\n")
                    f.write(f"- **Word Count:** {word_count} words (target: 100)\n")
                    f.write(f"- **Subtopics Generated:** {len(subtopics)}\n")
                    f.write(f"- **Readability Score:** {readability_score:.1f}/100\n")
                    f.write(f"- **SEO Score:** {seo_score:.1f}/100\n")
                    f.write(f"- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"- **API:** DataForSEO Content Generation API\n")
                    f.write(f"- **Cost:** ${total_cost:.5f}\n")
                    f.write(f"- **Tokens Used:** {total_tokens}\n")
                
                print(f"{Colors.OKGREEN}✓ Blog saved to: {output_file}{Colors.ENDC}\n")
                
                return result
                
            else:
                print(f"{Colors.FAIL}❌ Request failed with status {response.status_code}{Colors.ENDC}")
                print(f"{Colors.FAIL}Response: {response.text[:500]}{Colors.ENDC}")
                return None
                
    except httpx.TimeoutException:
        print(f"{Colors.FAIL}❌ Request timed out after 120 seconds{Colors.ENDC}")
        return None
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    try:
        result = asyncio.run(test_enhanced_endpoint())
        if result:
            print(f"\n{Colors.OKGREEN}{'='*80}{Colors.ENDC}")
            print(f"{Colors.OKGREEN}Test completed successfully!{Colors.ENDC}")
            print(f"{Colors.OKGREEN}{'='*80}{Colors.ENDC}\n")
        else:
            print(f"\n{Colors.FAIL}Test failed!{Colors.ENDC}\n")
            exit(1)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Test interrupted{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.FAIL}Test failed: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        exit(1)

