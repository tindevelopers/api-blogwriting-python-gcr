#!/usr/bin/env python3
"""
Test script for blog generation endpoint without images.

This script tests the /api/v1/blog/generate-enhanced endpoint to verify:
1. Image generation has been removed
2. Endpoint completes faster (2-3 minutes instead of 4+)
3. Response structure is correct
"""

import json
import sys
import subprocess
import time
from datetime import datetime

API_URL = "https://blog-writer-api-dev-613248238610.europe-west9.run.app"

def run_test(name, method, endpoint, data=None, timeout=300):
    """Run a test and return results."""
    print(f"\n{'='*60}")
    print(f"{name}")
    print(f"{'='*60}")
    print(f"Endpoint: {API_URL}{endpoint}")
    if data:
        print(f"Request: {json.dumps(data, indent=2)[:200]}...")
    print(f"{'='*60}\n")
    
    cmd = ["curl", "-s", "-X", method, f"{API_URL}{endpoint}"]
    if data:
        cmd.extend(["-H", "Content-Type: application/json", "-d", json.dumps(data)])
    
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        elapsed_time = time.time() - start_time
        
        if result.returncode != 0:
            print(f"❌ FAILED: curl error")
            print(f"Error: {result.stderr}")
            return None, elapsed_time
        
        try:
            response = json.loads(result.stdout)
            return response, elapsed_time
        except json.JSONDecodeError:
            print(f"⚠️  Response is not JSON")
            print(f"Response preview: {result.stdout[:500]}")
            return None, elapsed_time
    except subprocess.TimeoutExpired:
        elapsed_time = time.time() - start_time
        print(f"⏱️  TIMEOUT after {timeout}s")
        return None, elapsed_time
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"❌ ERROR: {e}")
        return None, elapsed_time

def analyze_response(response, elapsed_time):
    """Analyze the blog generation response."""
    if not response:
        return
    
    print(f"\n{'='*60}")
    print("Response Analysis")
    print(f"{'='*60}\n")
    
    # Check basic fields
    print(f"✅ Response received in {elapsed_time:.1f} seconds")
    print(f"   Status: {'SUCCESS' if response.get('success') else 'FAILED'}")
    
    # Check for images
    generated_images = response.get('generated_images')
    if generated_images is None:
        print(f"✅ Image generation removed: generated_images = null")
    elif generated_images == []:
        print(f"✅ Image generation removed: generated_images = []")
    else:
        print(f"⚠️  WARNING: Images still present: {len(generated_images)} images")
    
    # Check warnings
    warnings = response.get('warnings', [])
    if warnings:
        print(f"⚠️  Warnings: {len(warnings)}")
        for warning in warnings[:3]:
            print(f"   - {warning}")
    else:
        print(f"✅ No warnings")
    
    # Check blog content
    if response.get('title'):
        print(f"\n📝 Blog Content:")
        print(f"   Title: {response.get('title', 'N/A')[:80]}...")
        print(f"   Content length: {len(response.get('content', ''))} characters")
        print(f"   Word count: ~{len(response.get('content', '').split())} words")
    
    # Check progress updates
    progress_updates = response.get('progress_updates', [])
    if progress_updates:
        print(f"\n📊 Progress Updates: {len(progress_updates)} updates")
        print(f"   Stages tracked:")
        stages = {}
        for update in progress_updates:
            stage = update.get('stage', 'unknown')
            if stage not in stages:
                stages[stage] = update.get('status', 'N/A')
        
        for stage, status in list(stages.items())[:5]:
            print(f"   - {stage}: {status[:60]}...")
    else:
        print(f"\n⚠️  No progress updates in response")
    
    # Check metrics
    print(f"\n📈 Metrics:")
    print(f"   SEO Score: {response.get('seo_score', 'N/A')}")
    print(f"   Readability Score: {response.get('readability_score', 'N/A')}")
    print(f"   Quality Score: {response.get('quality_score', 'N/A')}")
    print(f"   Generation Time: {response.get('generation_time', 'N/A')}s")
    print(f"   Total Cost: ${response.get('total_cost', 0):.4f}")
    print(f"   Total Tokens: {response.get('total_tokens', 'N/A')}")
    
    # Check stage results
    stage_results = response.get('stage_results', [])
    if stage_results:
        print(f"\n🔧 Stage Results: {len(stage_results)} stages")
        for stage in stage_results[:3]:
            print(f"   - {stage.get('stage', 'unknown')}: {stage.get('provider', 'N/A')} ({stage.get('tokens', 0)} tokens)")

def main():
    """Run blog generation test."""
    print("\n" + "="*60)
    print("Blog Generation Test - Without Images")
    print("="*60)
    print(f"Testing: {API_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Test request
    test_request = {
        "topic": "Best Notary Services in California",
        "keywords": ["notary services california", "notary public california"],
        "tone": "professional",
        "length": "medium",
        "use_google_search": True,
        "use_citations": True,
        "use_serp_optimization": False,
        "use_knowledge_graph": False,
        "use_semantic_keywords": False,
        "use_quality_scoring": False,
        "use_consensus_generation": False
    }
    
    print("\n⏱️  Starting blog generation...")
    print("   Expected completion: 2-3 minutes (previously 4+ minutes)")
    print("   Monitoring for image generation removal...\n")
    
    # Run test
    response, elapsed_time = run_test(
        "Blog Generation Test",
        "POST",
        "/api/v1/blog/generate-enhanced",
        data=test_request,
        timeout=300  # 5 minutes max
    )
    
    # Analyze results
    if response:
        analyze_response(response, elapsed_time)
        
        # Performance check
        print(f"\n{'='*60}")
        print("Performance Check")
        print(f"{'='*60}\n")
        
        if elapsed_time < 180:  # Less than 3 minutes
            print(f"✅ EXCELLENT: Completed in {elapsed_time:.1f}s (< 3 minutes)")
            print(f"   Improvement: ~30-50% faster than before")
        elif elapsed_time < 240:  # Less than 4 minutes
            print(f"✅ GOOD: Completed in {elapsed_time:.1f}s (< 4 minutes)")
            print(f"   Improvement: Faster than before")
        else:
            print(f"⚠️  SLOW: Completed in {elapsed_time:.1f}s (>= 4 minutes)")
            print(f"   May still have performance issues")
        
        # Image removal check
        print(f"\n{'='*60}")
        print("Image Generation Removal Check")
        print(f"{'='*60}\n")
        
        generated_images = response.get('generated_images')
        if generated_images is None or generated_images == []:
            print(f"✅ SUCCESS: Image generation removed")
            print(f"   generated_images: {generated_images}")
        else:
            print(f"❌ FAILED: Images still being generated")
            print(f"   generated_images: {len(generated_images)} images")
        
        warnings = response.get('warnings', [])
        image_warnings = [w for w in warnings if 'image' in w.lower()]
        if image_warnings:
            print(f"⚠️  Image-related warnings found:")
            for warning in image_warnings:
                print(f"   - {warning}")
        else:
            print(f"✅ No image-related warnings")
        
    else:
        print(f"\n❌ Test failed or timed out")
        print(f"   Elapsed time: {elapsed_time:.1f}s")
        if elapsed_time >= 300:
            print(f"   ⚠️  Request timed out after 5 minutes")
    
    print(f"\n{'='*60}")
    print("Test Complete")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()

