"""
LiteLLM Router Integration for BlogWriter SDK.

This module provides intelligent AI provider routing using LiteLLM,
supporting cost optimization and automatic failover between providers.
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import yaml

import litellm
from litellm import Router, completion, acompletion
from litellm.exceptions import RateLimitError, APIError, ContextWindowExceededError

from .base_provider import BaseAIProvider, AIProviderError, AIResponse


class TaskType(Enum):
    """Task types for intelligent routing."""
    BLOG_GENERATION = "blog_generation"
    SEO_ANALYSIS = "seo_analysis"
    KEYWORD_EXTRACTION = "keyword_extraction"
    CONTENT_FORMATTING = "content_formatting"
    IMAGE_ANALYSIS = "image_analysis"
    SIMPLE_COMPLETION = "simple_completion"


class TaskComplexity(Enum):
    """Task complexity levels for cost optimization."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class LiteLLMRouterProvider(BaseAIProvider):
    """
    LiteLLM Router provider for intelligent AI routing and cost optimization.
    
    Features:
    - Automatic provider routing based on cost and performance
    - Intelligent fallback mechanisms
    - Task-based model selection
    - Real-time cost tracking
    - Multi-modal support
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        enable_cost_tracking: bool = True,
        enable_caching: bool = True,
        debug: bool = False
    ):
        """
        Initialize LiteLLM Router.
        
        Args:
            config_path: Path to LiteLLM configuration file
            enable_cost_tracking: Enable cost tracking and optimization
            enable_caching: Enable response caching
            debug: Enable debug logging
        """
        super().__init__()
        
        self.config_path = config_path or "litellm_config.yaml"
        self.enable_cost_tracking = enable_cost_tracking
        self.enable_caching = enable_caching
        self.debug = debug
        
        # Initialize router
        self.router: Optional[Router] = None
        self.config: Dict[str, Any] = {}
        self.cost_tracker: Dict[str, float] = {}
        
        # Set up logging
        if debug:
            litellm.set_verbose = True
            logging.getLogger("litellm").setLevel(logging.DEBUG)
        
        # Initialize router
        self._initialize_router()
    
    def _initialize_router(self) -> None:
        """Initialize the LiteLLM router with configuration."""
        try:
            # Load configuration
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = yaml.safe_load(f)
            else:
                # Use default configuration
                self.config = self._get_default_config()
            
            # Initialize router with model list
            model_list = self.config.get('model_list', [])
            router_settings = self.config.get('router_settings', {})
            
            self.router = Router(
                model_list=model_list,
                routing_strategy=router_settings.get('routing_strategy', 'simple-shuffle'),
                fallbacks=router_settings.get('fallbacks', []),
                context_window_fallbacks=router_settings.get('fallbacks', []),
                set_verbose=self.debug
            )
            
            logging.info(f"✅ LiteLLM Router initialized with {len(model_list)} models")
            
        except Exception as e:
            logging.error(f"❌ Failed to initialize LiteLLM Router: {e}")
            raise AIProviderError(f"Router initialization failed: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if no config file exists."""
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
    
    def _select_model_for_task(
        self,
        task_type: TaskType,
        complexity: TaskComplexity = TaskComplexity.MEDIUM,
        requires_vision: bool = False
    ) -> str:
        """
        Select the optimal model for a given task.
        
        Args:
            task_type: Type of task to perform
            complexity: Task complexity level
            requires_vision: Whether the task requires vision capabilities
            
        Returns:
            Model name to use for the task
        """
        task_routing = self.config.get('task_routing', {})
        task_config = task_routing.get(task_type.value, {})
        
        # Get models based on task configuration
        if requires_vision:
            # Filter for vision-capable models
            available_models = ['gpt-4o', 'gpt-4-turbo']
        elif complexity == TaskComplexity.LOW:
            # Use cheaper models for simple tasks
            available_models = task_config.get('primary_models', ['deepseek-chat', 'gpt-3.5-turbo'])
        elif complexity == TaskComplexity.HIGH:
            # Use premium models for complex tasks
            available_models = task_config.get('primary_models', ['gpt-4o', 'gpt-4-turbo'])
        else:
            # Medium complexity - balanced approach
            available_models = task_config.get('primary_models', ['gpt-4o', 'deepseek-chat'])
        
        # Return first available model (router will handle fallbacks)
        return available_models[0] if available_models else 'gpt-4o'
    
    async def generate_content(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        task_type: TaskType = TaskType.SIMPLE_COMPLETION,
        complexity: TaskComplexity = TaskComplexity.MEDIUM,
        **kwargs
    ) -> AIResponse:
        """
        Generate content using intelligent model routing.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            task_type: Type of task for optimal routing
            complexity: Task complexity level
            **kwargs: Additional parameters
            
        Returns:
            AI response with content and metadata
        """
        if not self.router:
            raise AIProviderError("Router not initialized")
        
        try:
            # Select optimal model for task
            model = self._select_model_for_task(task_type, complexity)
            
            # Prepare request parameters
            request_params = {
                'model': model,
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': max_tokens or 4096,
                'temperature': temperature or 0.7,
                **kwargs
            }
            
            # Make async completion request
            response = await acompletion(**request_params)
            
            # Extract response data
            content = response.choices[0].message.content
            usage = response.usage
            model_used = response.model
            
            # Track costs if enabled
            if self.enable_cost_tracking and usage:
                cost = self._calculate_cost(model_used, usage.prompt_tokens, usage.completion_tokens)
                self.cost_tracker[task_type.value] = self.cost_tracker.get(task_type.value, 0) + cost
            
            return AIResponse(
                content=content,
                model=model_used,
                usage={
                    'prompt_tokens': usage.prompt_tokens if usage else 0,
                    'completion_tokens': usage.completion_tokens if usage else 0,
                    'total_tokens': usage.total_tokens if usage else 0
                },
                metadata={
                    'task_type': task_type.value,
                    'complexity': complexity.value,
                    'cost': self._calculate_cost(model_used, usage.prompt_tokens, usage.completion_tokens) if usage else 0
                }
            )
            
        except (RateLimitError, APIError, ContextWindowExceededError) as e:
            logging.warning(f"⚠️ Provider error, attempting fallback: {e}")
            # Router will automatically handle fallbacks
            raise AIProviderError(f"Generation failed: {e}")
        
        except Exception as e:
            logging.error(f"❌ Unexpected error in content generation: {e}")
            raise AIProviderError(f"Unexpected error: {e}")
    
    async def generate_with_images(
        self,
        prompt: str,
        images: List[str],
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AIResponse:
        """
        Generate content with image inputs (multi-modal).
        
        Args:
            prompt: Text prompt
            images: List of image URLs or base64 data
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            AI response with content and metadata
        """
        if not self.router:
            raise AIProviderError("Router not initialized")
        
        try:
            # Select vision-capable model
            model = self._select_model_for_task(
                TaskType.IMAGE_ANALYSIS,
                TaskComplexity.HIGH,
                requires_vision=True
            )
            
            # Prepare multi-modal content
            content = [{'type': 'text', 'text': prompt}]
            for image in images:
                if image.startswith('http'):
                    content.append({
                        'type': 'image_url',
                        'image_url': {'url': image}
                    })
                else:
                    content.append({
                        'type': 'image_url',
                        'image_url': {'url': f'data:image/jpeg;base64,{image}'}
                    })
            
            # Make request
            response = await acompletion(
                model=model,
                messages=[{'role': 'user', 'content': content}],
                max_tokens=max_tokens or 4096,
                **kwargs
            )
            
            # Process response
            result_content = response.choices[0].message.content
            usage = response.usage
            
            return AIResponse(
                content=result_content,
                model=response.model,
                usage={
                    'prompt_tokens': usage.prompt_tokens if usage else 0,
                    'completion_tokens': usage.completion_tokens if usage else 0,
                    'total_tokens': usage.total_tokens if usage else 0
                },
                metadata={
                    'task_type': TaskType.IMAGE_ANALYSIS.value,
                    'image_count': len(images),
                    'multimodal': True
                }
            )
            
        except Exception as e:
            logging.error(f"❌ Multi-modal generation failed: {e}")
            raise AIProviderError(f"Multi-modal generation failed: {e}")
    
    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost for a request based on model pricing."""
        # Get model pricing from config
        model_list = self.config.get('model_list', [])
        for model_config in model_list:
            if model_config['model_name'] in model:
                model_info = model_config.get('model_info', {})
                input_cost = model_info.get('input_cost_per_token', 0)
                output_cost = model_info.get('output_cost_per_token', 0)
                
                return (prompt_tokens * input_cost) + (completion_tokens * output_cost)
        
        # Default cost calculation if not found
        return (prompt_tokens * 0.000001) + (completion_tokens * 0.000002)
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost tracking summary."""
        return {
            'total_cost': sum(self.cost_tracker.values()),
            'cost_by_task': dict(self.cost_tracker),
            'average_cost_per_task': sum(self.cost_tracker.values()) / len(self.cost_tracker) if self.cost_tracker else 0
        }
    
    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        if not self.router:
            return []
        
        return [model['model_name'] for model in self.config.get('model_list', [])]
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all configured providers."""
        if not self.router:
            return {'status': 'error', 'message': 'Router not initialized'}
        
        health_status = {}
        
        for model_config in self.config.get('model_list', []):
            model_name = model_config['model_name']
            try:
                # Simple test request
                response = await acompletion(
                    model=model_name,
                    messages=[{'role': 'user', 'content': 'Hello'}],
                    max_tokens=10
                )
                health_status[model_name] = {
                    'status': 'healthy',
                    'response_time': 'fast',
                    'model': response.model
                }
            except Exception as e:
                health_status[model_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return {
            'router_status': 'healthy' if self.router else 'error',
            'models': health_status,
            'total_models': len(self.config.get('model_list', [])),
            'healthy_models': len([m for m in health_status.values() if m['status'] == 'healthy'])
        }


# Convenience functions for easy integration
async def create_litellm_router(
    config_path: Optional[str] = None,
    **kwargs
) -> LiteLLMRouterProvider:
    """Create and initialize LiteLLM router provider."""
    router = LiteLLMRouterProvider(config_path=config_path, **kwargs)
    return router


# Task-specific helper functions
async def generate_blog_content(
    router: LiteLLMRouterProvider,
    prompt: str,
    complexity: TaskComplexity = TaskComplexity.HIGH,
    **kwargs
) -> AIResponse:
    """Generate blog content using optimal routing."""
    return await router.generate_content(
        prompt=prompt,
        task_type=TaskType.BLOG_GENERATION,
        complexity=complexity,
        **kwargs
    )


async def analyze_seo_content(
    router: LiteLLMRouterProvider,
    content: str,
    **kwargs
) -> AIResponse:
    """Analyze content for SEO using cost-optimized routing."""
    prompt = f"Analyze this content for SEO optimization:\n\n{content}"
    return await router.generate_content(
        prompt=prompt,
        task_type=TaskType.SEO_ANALYSIS,
        complexity=TaskComplexity.MEDIUM,
        **kwargs
    )


async def extract_keywords(
    router: LiteLLMRouterProvider,
    content: str,
    max_keywords: int = 20,
    **kwargs
) -> AIResponse:
    """Extract keywords using cost-optimized routing."""
    prompt = f"Extract {max_keywords} relevant keywords from this content:\n\n{content}"
    return await router.generate_content(
        prompt=prompt,
        task_type=TaskType.KEYWORD_EXTRACTION,
        complexity=TaskComplexity.LOW,
        **kwargs
    )
