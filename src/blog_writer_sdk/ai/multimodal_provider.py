"""Multi-modal AI provider implementations."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union
import base64
import httpx
from io import BytesIO
from PIL import Image

from .base_provider import BaseAIProvider, AIResponse
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider


class MultiModalProvider(ABC):
    """Abstract base class for multi-modal AI providers."""
    
    @abstractmethod
    async def analyze_image_content(
        self, 
        prompt: str, 
        image_data: Union[str, bytes], 
        image_type: str = "url"
    ) -> AIResponse:
        """Analyze content with image input."""
        pass
    
    @abstractmethod
    async def generate_content_from_media(
        self, 
        prompt: str, 
        media_items: List[Dict[str, Any]]
    ) -> AIResponse:
        """Generate content from multiple media inputs."""
        pass


class MultiModalOpenAIProvider(OpenAIProvider, MultiModalProvider):
    """OpenAI provider with multi-modal capabilities."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        super().__init__(api_key, model)
        # Ensure we're using a vision-capable model
        if "vision" not in model and "4o" not in model and "gpt-4" not in model:
            self.model = "gpt-4o"
    
    async def analyze_image_content(
        self, 
        prompt: str, 
        image_data: Union[str, bytes], 
        image_type: str = "url"
    ) -> AIResponse:
        """Analyze content with image input."""
        try:
            content = [{"type": "text", "text": prompt}]
            
            if image_type == "url":
                content.append({
                    "type": "image_url",
                    "image_url": {"url": image_data}
                })
            elif image_type == "base64":
                if isinstance(image_data, bytes):
                    image_data = base64.b64encode(image_data).decode()
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                })
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": content}],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return AIResponse(
                content=response.choices[0].message.content,
                model=self.model,
                provider="openai_multimodal",
                tokens_used=response.usage.total_tokens if response.usage else 0
            )
            
        except Exception as e:
            return AIResponse(
                content="",
                model=self.model,
                provider="openai_multimodal",
                error=str(e)
            )
    
    async def generate_content_from_media(
        self, 
        prompt: str, 
        media_items: List[Dict[str, Any]]
    ) -> AIResponse:
        """Generate content from multiple media inputs."""
        try:
            content = [{"type": "text", "text": prompt}]
            
            for item in media_items:
                if item["type"] == "image":
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": item["url"]}
                    })
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": content}],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return AIResponse(
                content=response.choices[0].message.content,
                model=self.model,
                provider="openai_multimodal",
                tokens_used=response.usage.total_tokens if response.usage else 0
            )
            
        except Exception as e:
            return AIResponse(
                content="",
                model=self.model,
                provider="openai_multimodal",
                error=str(e)
            )


class MultiModalAnthropicProvider(AnthropicProvider, MultiModalProvider):
    """Anthropic provider with multi-modal capabilities."""
    
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        super().__init__(api_key, model)
        # Ensure we're using a vision-capable model
        if "claude-3" not in model:
            self.model = "claude-3-opus-20240229"
    
    async def analyze_image_content(
        self, 
        prompt: str, 
        image_data: Union[str, bytes], 
        image_type: str = "url"
    ) -> AIResponse:
        """Analyze content with image input."""
        try:
            content = [{"type": "text", "text": prompt}]
            
            if image_type == "url":
                # Download image and convert to base64
                async with httpx.AsyncClient() as client:
                    response = await client.get(image_data)
                    image_bytes = response.content
                    image_b64 = base64.b64encode(image_bytes).decode()
            elif image_type == "base64":
                if isinstance(image_data, bytes):
                    image_b64 = base64.b64encode(image_data).decode()
                else:
                    image_b64 = image_data
            
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": image_b64
                }
            })
            
            response = await self.client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": content}],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return AIResponse(
                content=response.content[0].text,
                model=self.model,
                provider="anthropic_multimodal",
                tokens_used=response.usage.input_tokens + response.usage.output_tokens if response.usage else 0
            )
            
        except Exception as e:
            return AIResponse(
                content="",
                model=self.model,
                provider="anthropic_multimodal",
                error=str(e)
            )
    
    async def generate_content_from_media(
        self, 
        prompt: str, 
        media_items: List[Dict[str, Any]]
    ) -> AIResponse:
        """Generate content from multiple media inputs."""
        try:
            content = [{"type": "text", "text": prompt}]
            
            for item in media_items:
                if item["type"] == "image":
                    # Download and encode image
                    async with httpx.AsyncClient() as client:
                        response = await client.get(item["url"])
                        image_bytes = response.content
                        image_b64 = base64.b64encode(image_bytes).decode()
                    
                    content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_b64
                        }
                    })
            
            response = await self.client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": content}],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return AIResponse(
                content=response.content[0].text,
                model=self.model,
                provider="anthropic_multimodal",
                tokens_used=response.usage.input_tokens + response.usage.output_tokens if response.usage else 0
            )
            
        except Exception as e:
            return AIResponse(
                content="",
                model=self.model,
                provider="anthropic_multimodal",
                error=str(e)
            )


# Utility functions for image processing
async def download_image(url: str) -> bytes:
    """Download image from URL."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.content


def encode_image_to_base64(image_bytes: bytes) -> str:
    """Encode image bytes to base64 string."""
    return base64.b64encode(image_bytes).decode()


def resize_image(image_bytes: bytes, max_size: tuple = (1024, 1024)) -> bytes:
    """Resize image to fit within max_size while maintaining aspect ratio."""
    image = Image.open(BytesIO(image_bytes))
    image.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    output = BytesIO()
    image.save(output, format='JPEG', quality=85)
    return output.getvalue()
