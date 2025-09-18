#!/usr/bin/env python3
"""
Test script to verify Supabase database connection and configuration.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add src to path
sys.path.append('src')

def test_supabase_import():
    """Test if Supabase package can be imported."""
    try:
        from supabase import create_client, Client
        print("✅ Supabase package imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import Supabase: {e}")
        return False

def test_environment_variables():
    """Test if required environment variables are set."""
    print("\n🔍 Checking environment variables...")
    
    # Load environment variables from .env file if it exists
    if os.path.exists('.env'):
        load_dotenv('.env')
        print("✅ Loaded .env file")
    
    required_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value and value != f"your-{var.lower().replace('_', '-')}-here":
            print(f"✅ {var}: {'*' * 20}...{value[-4:] if len(value) > 4 else '****'}")
        else:
            print(f"❌ {var}: Not set or using placeholder value")
            missing_vars.append(var)
    
    return len(missing_vars) == 0

async def test_supabase_connection():
    """Test actual connection to Supabase."""
    try:
        from supabase import create_client, Client
        from src.blog_writer_sdk.integrations.supabase_client import SupabaseClient
        
        print("\n🔗 Testing Supabase connection...")
        
        # Get environment variables
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            print("❌ Missing Supabase credentials")
            return False
        
        # Test basic connection
        client = create_client(supabase_url, supabase_key)
        
        # Try to get project info (this will fail if credentials are wrong)
        try:
            # Simple test query - try to access a table
            # This will work even if tables don't exist yet
            result = client.table("_test_connection").select("*").limit(1).execute()
            print("✅ Basic Supabase connection successful")
        except Exception as e:
            if "JWT" in str(e) or "invalid" in str(e).lower():
                print(f"❌ Authentication failed: {e}")
                return False
            else:
                # Table doesn't exist, but connection is working
                print("✅ Supabase connection successful (table doesn't exist yet, which is expected)")
        
        # Test our custom SupabaseClient
        print("\n🧪 Testing custom SupabaseClient...")
        try:
            supabase_client = SupabaseClient(
                supabase_url=supabase_url,
                supabase_key=supabase_key,
                environment="test"
            )
            print("✅ SupabaseClient initialized successfully")
            
            # Test table name generation
            table_name = supabase_client._get_table_name("blog_posts")
            print(f"✅ Table name generation: {table_name}")
            
            return True
            
        except Exception as e:
            print(f"❌ SupabaseClient initialization failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Supabase connection test failed: {e}")
        return False

def test_database_schema():
    """Test database schema generation."""
    try:
        from src.blog_writer_sdk.integrations.supabase_client import SupabaseClient
        
        print("\n📋 Testing database schema generation...")
        
        # Create a test client (won't actually connect)
        supabase_client = SupabaseClient(
            supabase_url="https://test.supabase.co",
            supabase_key="test-key",
            environment="test"
        )
        
        # Generate schema
        schema = supabase_client.create_database_schema(create_all_environments=False)
        
        if "CREATE TABLE" in schema and "blog_posts_test" in schema:
            print("✅ Database schema generation successful")
            print(f"✅ Schema includes {schema.count('CREATE TABLE')} tables")
            return True
        else:
            print("❌ Database schema generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Database schema test failed: {e}")
        return False

async def main():
    """Main test function."""
    print("🚀 Supabase Connection Test")
    print("=" * 50)
    
    # Test 1: Import
    if not test_supabase_import():
        print("\n❌ Cannot proceed without Supabase package")
        return
    
    # Test 2: Environment variables
    env_ok = test_environment_variables()
    
    # Test 3: Connection (only if env vars are set)
    if env_ok:
        connection_ok = await test_supabase_connection()
    else:
        print("\n⚠️  Skipping connection test due to missing environment variables")
        connection_ok = False
    
    # Test 4: Schema generation
    schema_ok = test_database_schema()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"  Supabase Package: {'✅' if test_supabase_import() else '❌'}")
    print(f"  Environment Variables: {'✅' if env_ok else '❌'}")
    print(f"  Database Connection: {'✅' if connection_ok else '❌'}")
    print(f"  Schema Generation: {'✅' if schema_ok else '❌'}")
    
    if env_ok and connection_ok and schema_ok:
        print("\n🎉 All tests passed! Supabase is properly configured.")
    else:
        print("\n⚠️  Some tests failed. Check the configuration.")
        
        if not env_ok:
            print("\n💡 To fix environment variables:")
            print("   1. Copy env.example to .env")
            print("   2. Update SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY with real values")
            print("   3. Run this test again")

if __name__ == "__main__":
    asyncio.run(main())
