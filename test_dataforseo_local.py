#!/usr/bin/env python3
"""Test DataForSEO endpoints locally to inspect response structure."""

import asyncio
import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.blog_writer_sdk.integrations.dataforseo_integration import DataForSEOClient

async def test_related_keywords():
    """Test related keywords endpoint and inspect response."""
    print("="*80)
    print("Testing DataForSEO Related Keywords Endpoint")
    print("="*80)
    
    # Initialize client
    client = DataForSEOClient()
    
    # Clear cache
    client._cache = {}
    
    # Get credentials from env
    tenant_id = os.getenv("TENANT_ID", "default")
    await client.initialize_credentials(tenant_id)
    
    if not client.is_configured:
        print("❌ DataForSEO not configured. Set DATAFORSEO_API_KEY and DATAFORSEO_API_SECRET")
        return
    
    print(f"✅ DataForSEO configured")
    print(f"   API Key: {client.api_key[:10]}...")
    print(f"   Location: {client.location}")
    print(f"   Language: {client.language_code}")
    print()
    
    # Test related keywords
    print("📡 Calling get_related_keywords('pet grooming')...")
    try:
        response = await client.get_related_keywords(
            keyword="pet grooming",
            location_name="United States",
            language_code="en",
            tenant_id=tenant_id,
            depth=1,
            limit=5
        )
        
        print("\n" + "="*80)
        print("RESPONSE STRUCTURE:")
        print("="*80)
        print(f"Type: {type(response)}")
        print(f"Is dict: {isinstance(response, dict)}")
        
        if isinstance(response, dict):
            print(f"\nTop-level keys: {list(response.keys())}")
            print(f"\nStatus Code: {response.get('status_code')}")
            print(f"Status Message: {response.get('status_message')}")
            print(f"Tasks Count: {response.get('tasks_count')}")
            print(f"Tasks Error: {response.get('tasks_error')}")
            
            tasks = response.get("tasks")
            print(f"\nTasks type: {type(tasks)}")
            print(f"Tasks is None: {tasks is None}")
            print(f"Tasks is list: {isinstance(tasks, list)}")
            
            if isinstance(tasks, list) and len(tasks) > 0:
                first_task = tasks[0]
                print(f"\nFirst task type: {type(first_task)}")
                print(f"First task is None: {first_task is None}")
                print(f"First task is dict: {isinstance(first_task, dict)}")
                
                if isinstance(first_task, dict):
                    print(f"\nFirst task keys: {list(first_task.keys())}")
                    print(f"Task status_code: {first_task.get('status_code')}")
                    print(f"Task status_message: {first_task.get('status_message')}")
                    print(f"Task result type: {type(first_task.get('result'))}")
                    print(f"Task result: {first_task.get('result')}")
                    
                    # Pretty print full task
                    print("\n" + "="*80)
                    print("FULL FIRST TASK:")
                    print("="*80)
                    print(json.dumps(first_task, indent=2, default=str))
            else:
                print(f"\nTasks: {tasks}")
        
        print("\n" + "="*80)
        print("FULL RESPONSE:")
        print("="*80)
        print(json.dumps(response, indent=2, default=str))
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

async def test_keyword_ideas():
    """Test keyword ideas endpoint and inspect response."""
    print("\n\n" + "="*80)
    print("Testing DataForSEO Keyword Ideas Endpoint")
    print("="*80)
    
    # Initialize client
    client = DataForSEOClient()
    
    # Clear cache
    client._cache = {}
    
    # Get credentials from env
    tenant_id = os.getenv("TENANT_ID", "default")
    await client.initialize_credentials(tenant_id)
    
    print("📡 Calling get_keyword_ideas(['pet grooming'])...")
    try:
        response = await client.get_keyword_ideas(
            keywords=["pet grooming"],
            location_name="United States",
            language_code="en",
            tenant_id=tenant_id,
            limit=10
        )
        
        print("\n" + "="*80)
        print("RESPONSE STRUCTURE:")
        print("="*80)
        print(f"Type: {type(response)}")
        print(f"Is list: {isinstance(response, list)}")
        print(f"Length: {len(response) if isinstance(response, list) else 'N/A'}")
        
        if isinstance(response, list) and len(response) > 0:
            print(f"\nFirst item type: {type(response[0])}")
            print(f"First item keys: {list(response[0].keys()) if isinstance(response[0], dict) else 'N/A'}")
            print(f"\nFirst item:")
            print(json.dumps(response[0], indent=2, default=str))
        else:
            print(f"\nResponse: {response}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_related_keywords())
    asyncio.run(test_keyword_ideas())

