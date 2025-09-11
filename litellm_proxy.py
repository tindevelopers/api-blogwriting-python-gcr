#!/usr/bin/env python3
"""
LiteLLM Proxy Server for BlogWriter SDK.

This script starts a LiteLLM proxy server that provides a unified API
for multiple AI providers with intelligent routing and cost optimization.
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    import litellm
    from litellm import Router
    import uvicorn
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    import yaml
except ImportError as e:
    print(f"❌ Missing required dependencies: {e}")
    print("💡 Run: pip install litellm uvicorn fastapi pyyaml")
    sys.exit(1)


def load_config(config_path: str = "litellm_config.yaml") -> dict:
    """Load LiteLLM configuration from YAML file."""
    if not os.path.exists(config_path):
        print(f"⚠️ Config file not found: {config_path}")
        print("🔧 Using default configuration...")
        return get_default_config()
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        print(f"✅ Loaded configuration from: {config_path}")
        return config
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        print("🔧 Using default configuration...")
        return get_default_config()


def get_default_config() -> dict:
    """Get default LiteLLM configuration."""
    return {
        'model_list': [
            {
                'model_name': 'gpt-4o',
                'litellm_params': {
                    'model': 'openai/gpt-4o',
                    'api_key': os.environ.get('OPENAI_API_KEY'),
                    'max_tokens': 4096,
                    'temperature': 0.7
                }
            },
            {
                'model_name': 'deepseek-chat',
                'litellm_params': {
                    'model': 'deepseek/deepseek-chat',
                    'api_key': os.environ.get('DEEPSEEK_API_KEY'),
                    'api_base': 'https://api.deepseek.com',
                    'max_tokens': 4096,
                    'temperature': 0.7
                }
            }
        ],
        'router_settings': {
            'routing_strategy': 'cost-based-routing',
            'fallbacks': [['gpt-4o', 'deepseek-chat']]
        }
    }


def create_proxy_app(config: dict) -> FastAPI:
    """Create FastAPI app with LiteLLM proxy."""
    app = FastAPI(
        title="BlogWriter LiteLLM Proxy",
        description="Intelligent AI provider routing for BlogWriter SDK",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize router
    model_list = config.get('model_list', [])
    router_settings = config.get('router_settings', {})
    
    try:
        router = Router(
            model_list=model_list,
            routing_strategy=router_settings.get('routing_strategy', 'simple-shuffle'),
            fallbacks=router_settings.get('fallbacks', []),
            context_window_fallbacks=router_settings.get('fallbacks', []),
            set_verbose=True
        )
        
        print(f"✅ LiteLLM Router initialized with {len(model_list)} models")
        
        # Store router in app state
        app.state.router = router
        app.state.config = config
        
    except Exception as e:
        print(f"❌ Failed to initialize LiteLLM Router: {e}")
        sys.exit(1)
    
    return app


def main():
    """Main entry point for LiteLLM proxy server."""
    print("🚀 Starting BlogWriter LiteLLM Proxy Server...")
    
    # Load configuration
    config_path = os.getenv("LITELLM_CONFIG_PATH", "litellm_config.yaml")
    config = load_config(config_path)
    
    # Create proxy app
    app = create_proxy_app(config)
    
    # Add health check endpoint
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": "BlogWriter LiteLLM Proxy",
            "models": len(app.state.config.get('model_list', [])),
            "routing_strategy": app.state.config.get('router_settings', {}).get('routing_strategy', 'unknown')
        }
    
    # Add models endpoint
    @app.get("/models")
    async def list_models():
        models = app.state.config.get('model_list', [])
        return {
            "models": [model['model_name'] for model in models],
            "count": len(models)
        }
    
    # Proxy completion endpoint
    @app.post("/v1/chat/completions")
    async def proxy_completion(request: dict):
        try:
            # Use the router for completion
            response = await app.state.router.acompletion(**request)
            return response
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # Get server configuration
    host = os.getenv("LITELLM_HOST", "0.0.0.0")
    port = int(os.getenv("LITELLM_PORT", "8001"))
    
    print(f"🌐 Server will start on: http://{host}:{port}")
    print(f"📊 Health check: http://{host}:{port}/health")
    print(f"🤖 Models: http://{host}:{port}/models")
    print(f"🔗 OpenAI-compatible endpoint: http://{host}:{port}/v1/chat/completions")
    
    # Start server
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down LiteLLM Proxy Server...")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
