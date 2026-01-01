#!/usr/bin/env python3
"""
Test script to verify the DataForSEO status code fix locally.
This tests the generate_text method directly without starting the full server.
"""

import asyncio
import os
import sys
import json
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_dataforseo_status_code_fix():
    """Test that status code check is working in generate_text method."""
    
    print("=" * 60)
    print("Testing DataForSEO Status Code Fix")
    print("=" * 60)
    print()
    
    # Try to import DataForSEOClient
    try:
        from src.blog_writer_sdk.integrations.dataforseo_integration import DataForSEOClient
        print("✅ DataForSEOClient imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import DataForSEOClient: {e}")
        print("\nPlease install dependencies:")
        print("  pip install -r requirements.txt")
        return
    
    # Check for credentials
    api_key = os.getenv("DATAFORSEO_API_KEY")
    api_secret = os.getenv("DATAFORSEO_API_SECRET")
    
    if not api_key or not api_secret:
        print("⚠️  DataForSEO credentials not found in environment")
        print("Attempting to load from Google Secret Manager...")
        
        try:
            import subprocess
            api_key = subprocess.check_output([
                "gcloud", "secrets", "versions", "access", "latest",
                "--secret=DATAFORSEO_API_KEY",
                "--project=api-ai-blog-writer"
            ], stderr=subprocess.DEVNULL).decode().strip()
            
            api_secret = subprocess.check_output([
                "gcloud", "secrets", "versions", "access", "latest",
                "--secret=DATAFORSEO_API_SECRET",
                "--project=api-ai-blog-writer"
            ], stderr=subprocess.DEVNULL).decode().strip()
            
            print("✅ Credentials loaded from Secret Manager")
        except Exception as e:
            print(f"❌ Failed to load credentials: {e}")
            print("\nPlease set environment variables:")
            print("  export DATAFORSEO_API_KEY=your_key")
            print("  export DATAFORSEO_API_SECRET=your_secret")
            return
    
    # Initialize client
    print("\n" + "=" * 60)
    print("Initializing DataForSEO Client")
    print("=" * 60)
    
    client = DataForSEOClient(api_key=api_key, api_secret=api_secret)
    
    # Test generate_text with a simple prompt
    print("\n" + "=" * 60)
    print("Testing generate_text Method")
    print("=" * 60)
    print()
    
    test_prompt = "Benefits of Python Programming"
    test_word_count = 100
    
    print(f"Prompt: {test_prompt}")
    print(f"Target Word Count: {test_word_count}")
    print()
    print("📡 Calling generate_text...")
    print()
    
    try:
        result = await client.generate_text(
            prompt=test_prompt,
            max_tokens=200,
            word_count=test_word_count,
            tenant_id="test"
        )
        
        print("=" * 60)
        print("Response Received")
        print("=" * 60)
        print()
        
        generated_text = result.get("text", "")
        tokens_used = result.get("tokens_used", 0)
        metadata = result.get("metadata", {})
        
        if generated_text:
            word_count = len(generated_text.split())
            print(f"✅ SUCCESS - Content Generated")
            print(f"   Word Count: {word_count} words")
            print(f"   Tokens Used: {tokens_used}")
            print(f"   Text Length: {len(generated_text)} chars")
            print()
            print("Content Preview (first 200 chars):")
            print("-" * 60)
            print(generated_text[:200] + "..." if len(generated_text) > 200 else generated_text)
            print()
        else:
            print("❌ FAILED - Empty content returned")
            print()
            print("This should NOT happen with the status code fix!")
            print("The fix should raise an error with the actual API status code")
            print("instead of returning empty content.")
            print()
            print("Check the logs above for the actual DataForSEO API error.")
            
    except ValueError as e:
        # This is the expected behavior with the fix!
        error_msg = str(e)
        print("=" * 60)
        print("✅ Status Code Fix Working!")
        print("=" * 60)
        print()
        print("The method correctly raised an error with the status code:")
        print("-" * 60)
        print(f"Error: {error_msg}")
        print("-" * 60)
        print()
        
        if "status_code" in error_msg:
            print("✅ Error message includes status_code (fix is working)")
        if "40204" in error_msg:
            print("⚠️  Status 40204: Subscription required")
            print("   Check DataForSEO plan includes Content Generation API")
        elif "40501" in error_msg:
            print("⚠️  Status 40501: Invalid field")
            print("   API format may have changed")
        else:
            print(f"⚠️  Status code: {error_msg}")
            print("   Check DataForSEO API documentation for this error")
            
    except Exception as e:
        print("=" * 60)
        print("❌ Unexpected Error")
        print("=" * 60)
        print()
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print()
        import traceback
        print("Traceback:")
        traceback.print_exc()
    
    print()
    print("=" * 60)
    print("Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_dataforseo_status_code_fix())

