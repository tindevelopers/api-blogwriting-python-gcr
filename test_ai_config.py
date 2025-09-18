#!/usr/bin/env python3
"""
Test script to check AI generation system configuration.
"""

import os
import sys

# Add src to path
sys.path.append('src')

def check_ai_environment_variables():
    """Check which AI providers are configured."""
    print("🤖 AI Generation System Configuration Check")
    print("=" * 50)
    
    ai_providers = {
        "OpenAI": {
            "url": "OPENAI_API_KEY",
            "org": "OPENAI_ORGANIZATION", 
            "model": "OPENAI_DEFAULT_MODEL"
        },
        "Anthropic": {
            "key": "ANTHROPIC_API_KEY",
            "model": "ANTHROPIC_DEFAULT_MODEL"
        },
        "Azure OpenAI": {
            "key": "AZURE_OPENAI_API_KEY",
            "endpoint": "AZURE_OPENAI_ENDPOINT",
            "model": "AZURE_OPENAI_DEFAULT_MODEL"
        },
        "DeepSeek": {
            "key": "DEEPSEEK_API_KEY",
            "base": "DEEPSEEK_API_BASE",
            "model": "DEEPSEEK_DEFAULT_MODEL"
        }
    }
    
    configured_providers = []
    
    for provider_name, config in ai_providers.items():
        print(f"\n🔍 Checking {provider_name}:")
        provider_configured = True
        
        for config_key, env_var in config.items():
            value = os.getenv(env_var)
            if value and not value.startswith("your-") and value != "your-service-role-key-here":
                print(f"  ✅ {config_key}: {'*' * 20}...{value[-4:] if len(value) > 4 else '****'}")
            else:
                print(f"  ❌ {config_key}: Not configured")
                provider_configured = False
        
        if provider_configured:
            configured_providers.append(provider_name)
            print(f"  🎉 {provider_name} is fully configured!")
        else:
            print(f"  ⚠️  {provider_name} needs configuration")
    
    return configured_providers

def check_ai_code_structure():
    """Check if AI provider code is properly structured."""
    print("\n📁 AI Code Structure Check:")
    
    ai_files = [
        "src/blog_writer_sdk/ai/base_provider.py",
        "src/blog_writer_sdk/ai/openai_provider.py", 
        "src/blog_writer_sdk/ai/anthropic_provider.py",
        "src/blog_writer_sdk/ai/ai_content_generator.py",
        "src/blog_writer_sdk/ai/blog_writer_abstraction.py"
    ]
    
    for file_path in ai_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - Missing!")

def check_main_ai_integration():
    """Check how AI is integrated in the main application."""
    print("\n🔗 Main Application AI Integration:")
    
    main_file = "main.py"
    if os.path.exists(main_file):
        with open(main_file, 'r') as f:
            content = f.read()
            
        ai_checks = [
            ("AIContentGenerator", "AI Content Generator import"),
            ("create_ai_content_generator", "AI generator creation function"),
            ("ai_generator", "AI generator instance"),
            ("enable_ai_enhancement", "AI enhancement flag")
        ]
        
        for check, description in ai_checks:
            if check in content:
                print(f"  ✅ {description}")
            else:
                print(f"  ❌ {description} - Not found")
    else:
        print("  ❌ main.py not found")

def main():
    """Main test function."""
    # Check environment variables
    configured_providers = check_ai_environment_variables()
    
    # Check code structure
    check_ai_code_structure()
    
    # Check main integration
    check_main_ai_integration()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 AI Configuration Summary:")
    
    if configured_providers:
        print(f"  ✅ Configured AI Providers: {', '.join(configured_providers)}")
        print(f"  🎯 Total: {len(configured_providers)} provider(s) ready")
    else:
        print("  ❌ No AI providers configured")
        print("  💡 To configure AI providers:")
        print("     1. Set environment variables for your preferred AI provider(s)")
        print("     2. Update .env file with real API keys")
        print("     3. Restart the application")
    
    print("\n🔧 Available AI Features:")
    print("  • Blog content generation")
    print("  • SEO optimization")
    print("  • Content analysis")
    print("  • Multi-provider fallback")
    print("  • Batch processing")
    print("  • Quality scoring")

if __name__ == "__main__":
    main()
