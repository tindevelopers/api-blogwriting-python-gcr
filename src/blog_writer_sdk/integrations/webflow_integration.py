"""
Webflow integration for the Blog Writer SDK.

This module provides integration with Webflow CMS for publishing blog posts,
managing collections, and handling media uploads.
"""

import os
import logging
import httpx
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import base64
import json

from ..models.blog_models import BlogPost, BlogGenerationResult


class WebflowClient:
    """
    Webflow client for blog writer operations.
    
    Handles publishing blog posts to Webflow CMS, managing collections,
    and uploading media assets.
    """
    
    def __init__(
        self,
        api_token: Optional[str] = None,
        site_id: Optional[str] = None,
        collection_id: Optional[str] = None,
    ):
        """
        Initialize Webflow client.
        
        Args:
            api_token: Webflow API token
            site_id: Webflow site ID
            collection_id: Webflow collection ID for blog posts
        """
        self.api_token = api_token or os.getenv("WEBFLOW_API_TOKEN")
        self.site_id = site_id or os.getenv("WEBFLOW_SITE_ID")
        self.collection_id = collection_id or os.getenv("WEBFLOW_COLLECTION_ID")
        
        if not self.api_token:
            raise ValueError("Webflow API token is required")
        
        self.base_url = "https://api.webflow.com/v2"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.logger = logging.getLogger(__name__)
    
    async def publish_blog_post(
        self, 
        blog_result: BlogGenerationResult,
        collection_id: Optional[str] = None,
        publish: bool = True
    ) -> Dict[str, Any]:
        """
        Publish a blog post to Webflow.
        
        Args:
            blog_result: Generated blog content
            collection_id: Target collection ID (overrides instance setting)
            publish: Whether to publish immediately
            
        Returns:
            Dictionary containing Webflow item details
        """
        target_collection_id = collection_id or self.collection_id
        
        if not target_collection_id:
            raise ValueError("Webflow collection ID is required")
        
        try:
            # Prepare content for Webflow
            webflow_content = await self._prepare_webflow_content(blog_result)
            
            # Create the blog post item
            item_data = {
                "fieldData": {
                    "name": blog_result.title,
                    "slug": self._generate_slug(blog_result.title),
                    "post-body": webflow_content["content"],
                    "post-summary": webflow_content["summary"],
                    "post-author": webflow_content.get("author", "AI Content Generator"),
                    "main-image": webflow_content.get("featured_image", ""),
                    "category": webflow_content.get("category", "General"),
                    "tags": webflow_content.get("tags", []),
                    "seo-title": webflow_content.get("seo_title", blog_result.title),
                    "seo-description": webflow_content.get("seo_description", webflow_content["summary"]),
                    "seo-keywords": webflow_content.get("keywords", []),
                }
            }
            
            async with httpx.AsyncClient() as client:
                # Create the item
                response = await client.post(
                    f"{self.base_url}/collections/{target_collection_id}/items",
                    headers=self.headers,
                    json=item_data,
                    timeout=30.0
                )
                response.raise_for_status()
                item_result = response.json()
                
                self.logger.info(f"Created Webflow item: {item_result['id']}")
                
                # Publish if requested
                if publish:
                    publish_result = await self._publish_item(item_result["id"])
                    item_result["published"] = publish_result
                
                return item_result
                
        except Exception as e:
            self.logger.error(f"Failed to publish to Webflow: {str(e)}")
            raise
    
    async def upload_media(
        self, 
        media_data: bytes, 
        filename: str,
        alt_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload media to Webflow.
        
        Args:
            media_data: Media file data
            filename: Original filename
            alt_text: Alt text for the media
            
        Returns:
            Dictionary containing media upload details
        """
        try:
            # Upload to Webflow assets
            async with httpx.AsyncClient() as client:
                files = {
                    "file": (filename, media_data, "application/octet-stream")
                }
                
                # Remove Content-Type header for file upload
                upload_headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}
                
                response = await client.post(
                    f"{self.base_url}/sites/{self.site_id}/assets",
                    headers=upload_headers,
                    files=files,
                    timeout=60.0
                )
                response.raise_for_status()
                
                asset_result = response.json()
                
                self.logger.info(f"Uploaded media to Webflow: {asset_result['id']}")
                
                return asset_result
                
        except Exception as e:
            self.logger.error(f"Failed to upload media to Webflow: {str(e)}")
            raise
    
    async def get_collections(self) -> List[Dict[str, Any]]:
        """
        Get all collections for the site.
        
        Returns:
            List of collection details
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/sites/{self.site_id}/collections",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                
                collections = response.json()
                return collections.get("items", [])
                
        except Exception as e:
            self.logger.error(f"Failed to get Webflow collections: {str(e)}")
            raise
    
    async def get_published_items(
        self, 
        collection_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get published items from a collection.
        
        Args:
            collection_id: Collection ID (uses default if not provided)
            limit: Maximum number of items to retrieve
            
        Returns:
            List of published items
        """
        target_collection_id = collection_id or self.collection_id
        
        if not target_collection_id:
            raise ValueError("Webflow collection ID is required")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/collections/{target_collection_id}/items",
                    headers=self.headers,
                    params={"limit": limit},
                    timeout=30.0
                )
                response.raise_for_status()
                
                items = response.json()
                return items.get("items", [])
                
        except Exception as e:
            self.logger.error(f"Failed to get Webflow items: {str(e)}")
            raise
    
    async def _prepare_webflow_content(self, blog_result: BlogGenerationResult) -> Dict[str, Any]:
        """Prepare blog content for Webflow format."""
        
        # Extract SEO data
        seo_data = blog_result.seo_data or {}
        
        # Generate summary from content
        content_preview = blog_result.content[:300] + "..." if len(blog_result.content) > 300 else blog_result.content
        
        # Extract images from content (if any)
        featured_image = ""
        if hasattr(blog_result, 'images') and blog_result.images:
            featured_image = blog_result.images[0].get('url', '')
        
        return {
            "content": blog_result.content,
            "summary": content_preview,
            "seo_title": seo_data.get("title", blog_result.title),
            "seo_description": seo_data.get("description", content_preview),
            "keywords": blog_result.keywords or [],
            "category": "AI Generated Content",
            "tags": blog_result.keywords or [],
            "featured_image": featured_image,
            "author": "AI Content Generator"
        }
    
    def _generate_slug(self, title: str) -> str:
        """Generate URL-friendly slug from title."""
        import re
        
        # Convert to lowercase and replace spaces with hyphens
        slug = title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)  # Remove special characters
        slug = re.sub(r'[-\s]+', '-', slug)   # Replace spaces and multiple hyphens
        slug = slug.strip('-')                # Remove leading/trailing hyphens
        
        # Add timestamp to ensure uniqueness
        timestamp = datetime.now().strftime("%Y%m%d")
        return f"{slug}-{timestamp}"
    
    async def _publish_item(self, item_id: str) -> Dict[str, Any]:
        """Publish a Webflow item."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.base_url}/collections/{self.collection_id}/items/{item_id}/publish",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                
                return response.json()
                
        except Exception as e:
            self.logger.error(f"Failed to publish Webflow item {item_id}: {str(e)}")
            raise


class WebflowPublisher:
    """
    High-level publisher for Webflow integration.
    
    Provides convenient methods for publishing blog content to Webflow
    with automatic media handling and content formatting.
    """
    
    def __init__(self, webflow_client: Optional[WebflowClient] = None):
        """
        Initialize Webflow publisher.
        
        Args:
            webflow_client: Webflow client instance
        """
        self.webflow_client = webflow_client or WebflowClient()
        self.logger = logging.getLogger(__name__)
    
    async def publish_with_media(
        self,
        blog_result: BlogGenerationResult,
        media_files: Optional[List[Dict[str, Any]]] = None,
        collection_id: Optional[str] = None,
        publish: bool = True
    ) -> Dict[str, Any]:
        """
        Publish blog post with associated media files.
        
        Args:
            blog_result: Generated blog content
            media_files: List of media files to upload
            collection_id: Target collection ID
            publish: Whether to publish immediately
            
        Returns:
            Dictionary containing publication details
        """
        try:
            published_media = []
            
            # Upload media files if provided
            if media_files:
                for media_file in media_files:
                    media_result = await self.webflow_client.upload_media(
                        media_data=media_file["data"],
                        filename=media_file["filename"],
                        alt_text=media_file.get("alt_text")
                    )
                    published_media.append(media_result)
            
            # Publish the blog post
            blog_result.images = published_media  # Attach uploaded media
            result = await self.webflow_client.publish_blog_post(
                blog_result=blog_result,
                collection_id=collection_id,
                publish=publish
            )
            
            result["uploaded_media"] = published_media
            
            self.logger.info(f"Successfully published blog to Webflow with {len(published_media)} media files")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to publish blog with media to Webflow: {str(e)}")
            raise
