#!/usr/bin/env python3
"""
Test script for image generation endpoint.

This script tests the /api/v1/images/generate endpoint to ensure it's working correctly.
"""

import os
import sys
import json
import subprocess
from typing import Optional, Dict, Any

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "https://blog-writer-api-dev-613248238610.europe-west9.run.app")
TEST_PROMPT = "A beautiful sunset over mountains, professional photography, high quality"


def test_image_generation_endpoint(
    prompt: str = TEST_PROMPT,
    style: Optional[str] = "photographic",
    aspect_ratio: Optional[str] = "16:9",
    quality: Optional[str] = "standard"
) -> Dict[str, Any]:
    """
    Test the image generation endpoint.
    
    Args:
        prompt: Text prompt for image generation
        style: Image style (optional)
        aspect_ratio: Aspect ratio (optional)
        quality: Image quality (optional)
    
    Returns:
        Dictionary with test results
    """
    endpoint = f"{API_BASE_URL}/api/v1/images/generate"
    
    print(f"\n{'='*60}")
    print(f"Testing Image Generation Endpoint")
    print(f"{'='*60}")
    print(f"Endpoint: {endpoint}")
    print(f"Prompt: {prompt}")
    print(f"Style: {style}")
    print(f"Aspect Ratio: {aspect_ratio}")
    print(f"Quality: {quality}")
    print(f"{'='*60}\n")
    
    # Prepare request
    request_data = {
        "prompt": prompt,
        "provider": "stability_ai"
    }
    
    if style:
        request_data["style"] = style
    if aspect_ratio:
        request_data["aspect_ratio"] = aspect_ratio
    if quality:
        request_data["quality"] = quality
    
    try:
        # Make request using curl
        print("Sending request...")
        curl_cmd = [
            "curl", "-s", "-X", "POST",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(request_data),
            endpoint
        ]
        
        result_proc = subprocess.run(
            curl_cmd,
            capture_output=True,
            text=True,
            timeout=120  # Image generation can take time
        )
        
        if result_proc.returncode != 0:
            print(f"❌ curl error: {result_proc.stderr}")
            return {
                "success": False,
                "error": f"curl error: {result_proc.stderr}"
            }
        
        # Parse response
        try:
            result = json.loads(result_proc.stdout)
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON response")
            print(f"Response: {result_proc.stdout[:500]}")
            return {
                "success": False,
                "error": "Invalid JSON response"
            }
        
        # Check response (assume 200 if we got JSON)
        if result.get('success') is not False and 'images' in result:
            
            print("\n✅ Request successful!")
            print(f"\nResponse Summary:")
            print(f"  Success: {result.get('success', False)}")
            print(f"  Provider: {result.get('provider', 'unknown')}")
            print(f"  Model: {result.get('model', 'N/A')}")
            print(f"  Generation Time: {result.get('generation_time_seconds', 0):.2f}s")
            print(f"  Images Generated: {len(result.get('images', []))}")
            
            if result.get('cost'):
                print(f"  Cost: ${result.get('cost', 0):.4f}")
            
            # Check images
            images = result.get('images', [])
            if images:
                print(f"\n📸 Generated Images:")
                for i, img in enumerate(images, 1):
                    print(f"  Image {i}:")
                    print(f"    ID: {img.get('image_id', 'N/A')}")
                    print(f"    Size: {img.get('width', 0)}x{img.get('height', 0)}")
                    print(f"    Format: {img.get('format', 'N/A')}")
                    if img.get('image_url'):
                        print(f"    URL: {img.get('image_url')[:80]}...")
                    elif img.get('image_data'):
                        data_len = len(img.get('image_data', ''))
                        print(f"    Data: Base64 encoded ({data_len} chars)")
                    if img.get('size_bytes'):
                        size_mb = img.get('size_bytes', 0) / (1024 * 1024)
                        print(f"    File Size: {size_mb:.2f} MB")
            else:
                print("\n⚠️  No images in response")
            
            if result.get('error_message'):
                print(f"\n⚠️  Error Message: {result.get('error_message')}")
            
            return {
                "success": True,
                "result": result,
                "images_count": len(images)
            }
        else:
            # Check for error messages
            error_msg = result.get('error_message') or result.get('detail', 'Unknown error')
            
            if 'no image providers' in error_msg.lower() or '503' in str(result):
                print(f"\n❌ Service Unavailable")
                print(f"Error: {error_msg}")
                print("\n💡 This usually means:")
                print("  1. STABILITY_AI_API_KEY is not configured")
                print("  2. No image providers are initialized")
                print("  3. Check Cloud Run secrets or environment variables")
                
                return {
                    "success": False,
                    "error": error_msg,
                    "suggestion": "Check STABILITY_AI_API_KEY configuration"
                }
            else:
                print(f"\n❌ Request failed")
                print(f"Error: {error_msg}")
                
                return {
                    "success": False,
                    "error": error_msg
                }
            
    except subprocess.TimeoutExpired:
        print("\n❌ Request timed out (>120s)")
        print("Image generation may be taking longer than expected")
        return {
            "success": False,
            "error": "Request timeout",
            "suggestion": "Image generation may still be processing"
        }
        
    except Exception as e:
        print(f"\n❌ Connection Error: {e}")
        print(f"Could not connect to {API_BASE_URL}")
        print("\n💡 Make sure:")
        print("  1. The API server is running")
        print("  2. The API_BASE_URL is correct")
        print("  3. Check firewall/network settings")
        
        return {
            "success": False,
            "error": f"Connection error: {str(e)}",
            "suggestion": "Check API server is running"
        }


def test_providers_endpoint() -> Dict[str, Any]:
    """Test the image providers status endpoint."""
    endpoint = f"{API_BASE_URL}/api/v1/images/providers"
    
    print(f"\n{'='*60}")
    print(f"Testing Image Providers Status")
    print(f"{'='*60}")
    print(f"Endpoint: {endpoint}")
    print(f"{'='*60}\n")
    
    try:
        curl_cmd = ["curl", "-s", "-X", "GET", endpoint]
        result_proc = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=10)
        
        if result_proc.returncode != 0:
            print(f"❌ curl error: {result_proc.stderr}")
            return {"success": False, "error": result_proc.stderr}
        
        try:
            providers = json.loads(result_proc.stdout)
            print("✅ Providers endpoint accessible")
            print(f"\nAvailable Providers: {len(providers.get('providers', []))}")
            
            for provider in providers.get('providers', []):
                print(f"\n  Provider: {provider.get('name', 'unknown')}")
                print(f"    Type: {provider.get('type', 'unknown')}")
                print(f"    Status: {provider.get('status', 'unknown')}")
                print(f"    Enabled: {provider.get('enabled', False)}")
            
            return {"success": True, "providers": providers}
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON response")
            print(f"Response: {result_proc.stdout[:200]}")
            return {"success": False, "error": "Invalid JSON"}
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Image Generation Endpoint Test Suite")
    print("="*60)
    
    # Test 1: Check providers status
    print("\n[Test 1] Checking image providers status...")
    providers_result = test_providers_endpoint()
    
    # Test 2: Generate image
    print("\n[Test 2] Testing image generation...")
    generation_result = test_image_generation_endpoint(
        prompt=TEST_PROMPT,
        style="photographic",
        aspect_ratio="16:9",
        quality="standard"
    )
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Providers Check: {'✅ PASS' if providers_result.get('success') else '❌ FAIL'}")
    print(f"Image Generation: {'✅ PASS' if generation_result.get('success') else '❌ FAIL'}")
    
    if generation_result.get('success'):
        print(f"\n✅ All tests passed!")
        print(f"   Generated {generation_result.get('images_count', 0)} image(s)")
    else:
        print(f"\n❌ Some tests failed")
        if generation_result.get('suggestion'):
            print(f"   Suggestion: {generation_result.get('suggestion')}")
    
    print("="*60 + "\n")
    
    # Return exit code
    if generation_result.get('success'):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

