"""
WordPress integration for the Blog Writer SDK.

This module provides integration with WordPress for publishing blog posts
via REST API, managing categories, tags, and media uploads.
"""

import os
import logging
import httpx
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import base64
import json

from ..models.blog_models import BlogPost, BlogGenerationResult


class WordPressClient:
    """
    WordPress client for blog writer operations.
    
    Handles publishing blog posts to WordPress via REST API,
    managing categories, tags, and media uploads.
    """
    
    def __init__(
        self,
        site_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        app_password: Optional[str] = None,
    ):
        """
        Initialize WordPress client.
        
        Args:
            site_url: WordPress site URL (e.g., 'https://yoursite.com')
            username: WordPress username
            password: WordPress password (or app password)
            app_password: WordPress application password (recommended)
        """
        self.site_url = site_url or os.getenv("WORDPRESS_SITE_URL")
        self.username = username or os.getenv("WORDPRESS_USERNAME")
        self.password = app_password or password or os.getenv("WORDPRESS_APP_PASSWORD")
        
        if not all([self.site_url, self.username, self.password]):
            raise ValueError("WordPress site URL, username, and password/app password are required")
        
        # Ensure site URL has proper format
        if not self.site_url.startswith('http'):
            self.site_url = f"https://{self.site_url}"
        
        self.api_url = f"{self.site_url}/wp-json/wp/v2"
        
        # Create authentication header
        credentials = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        self.headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.logger = logging.getLogger(__name__)
    
    async def publish_blog_post(
        self, 
        blog_result: BlogGenerationResult,
        status: str = "publish",
        categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        featured_media: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Publish a blog post to WordPress.
        
        Args:
            blog_result: Generated blog content
            status: Post status ('publish', 'draft', 'private')
            categories: List of category names or IDs
            tags: List of tag names
            featured_media: Featured media ID
            
        Returns:
            Dictionary containing WordPress post details
        """
        try:
            # Prepare content for WordPress
            wp_content = await self._prepare_wordpress_content(blog_result)
            
            # Resolve categories and tags to IDs
            category_ids = await self._resolve_categories(categories or [])
            tag_ids = await self._resolve_tags(tags or (blog_result.keywords or []))
            
            # Create the post
            post_data = {
                "title": blog_result.title,
                "content": wp_content["content"],
                "excerpt": wp_content["summary"],
                "status": status,
                "categories": category_ids,
                "tags": tag_ids,
                "meta": {
                    "seo_title": wp_content.get("seo_title", blog_result.title),
                    "seo_description": wp_content.get("seo_description", wp_content["summary"]),
                    "focus_keyword": blog_result.focus_keyword or "",
                    "generated_by": "AI Blog Writer SDK"
                }
            }
            
            if featured_media:
                post_data["featured_media"] = featured_media
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/posts",
                    headers=self.headers,
                    json=post_data,
                    timeout=30.0
                )
                response.raise_for_status()
                
                post_result = response.json()
                
                self.logger.info(f"Created WordPress post: {post_result['id']}")
                
                return post_result
                
        except Exception as e:
            self.logger.error(f"Failed to publish to WordPress: {str(e)}")
            raise
    
    async def upload_media(
        self, 
        media_data: bytes, 
        filename: str,
        alt_text: Optional[str] = None,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload media to WordPress.
        
        Args:
            media_data: Media file data
            filename: Original filename
            alt_text: Alt text for the media
            caption: Caption for the media
            
        Returns:
            Dictionary containing media upload details
        """
        try:
            # Prepare multipart form data
            files = {
                "file": (filename, media_data, self._get_content_type(filename))
            }
            
            data = {}
            if alt_text:
                data["alt_text"] = alt_text
            if caption:
                data["caption"] = caption
            
            async with httpx.AsyncClient() as client:
                # Remove Content-Type header for file upload
                upload_headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}
                
                response = await client.post(
                    f"{self.api_url}/media",
                    headers=upload_headers,
                    files=files,
                    data=data,
                    timeout=60.0
                )
                response.raise_for_status()
                
                media_result = response.json()
                
                self.logger.info(f"Uploaded media to WordPress: {media_result['id']}")
                
                return media_result
                
        except Exception as e:
            self.logger.error(f"Failed to upload media to WordPress: {str(e)}")
            raise
    
    async def get_categories(self) -> List[Dict[str, Any]]:
        """
        Get all categories.
        
        Returns:
            List of category details
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/categories",
                    headers=self.headers,
                    params={"per_page": 100},
                    timeout=30.0
                )
                response.raise_for_status()
                
                return response.json()
                
        except Exception as e:
            self.logger.error(f"Failed to get WordPress categories: {str(e)}")
            raise
    
    async def get_tags(self) -> List[Dict[str, Any]]:
        """
        Get all tags.
        
        Returns:
            List of tag details
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/tags",
                    headers=self.headers,
                    params={"per_page": 100},
                    timeout=30.0
                )
                response.raise_for_status()
                
                return response.json()
                
        except Exception as e:
            self.logger.error(f"Failed to get WordPress tags: {str(e)}")
            raise
    
    async def create_category(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new category.
        
        Args:
            name: Category name
            description: Category description
            
        Returns:
            Dictionary containing category details
        """
        try:
            category_data = {"name": name}
            if description:
                category_data["description"] = description
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/categories",
                    headers=self.headers,
                    json=category_data,
                    timeout=30.0
                )
                response.raise_for_status()
                
                return response.json()
                
        except Exception as e:
            self.logger.error(f"Failed to create WordPress category: {str(e)}")
            raise
    
    async def create_tag(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new tag.
        
        Args:
            name: Tag name
            description: Tag description
            
        Returns:
            Dictionary containing tag details
        """
        try:
            tag_data = {"name": name}
            if description:
                tag_data["description"] = description
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/tags",
                    headers=self.headers,
                    json=tag_data,
                    timeout=30.0
                )
                response.raise_for_status()
                
                return response.json()
                
        except Exception as e:
            self.logger.error(f"Failed to create WordPress tag: {str(e)}")
            raise
    
    async def get_posts(
        self, 
        status: str = "publish",
        per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get posts from WordPress.
        
        Args:
            status: Post status filter
            per_page: Number of posts per page
            
        Returns:
            List of posts
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/posts",
                    headers=self.headers,
                    params={"status": status, "per_page": per_page},
                    timeout=30.0
                )
                response.raise_for_status()
                
                return response.json()
                
        except Exception as e:
            self.logger.error(f"Failed to get WordPress posts: {str(e)}")
            raise
    
    async def _prepare_wordpress_content(self, blog_result: BlogGenerationResult) -> Dict[str, Any]:
        """Prepare blog content for WordPress format."""
        
        # Convert markdown to HTML for WordPress
        html_content = self._markdown_to_html(blog_result.content)
        
        # Extract SEO data
        seo_data = blog_result.seo_data or {}
        
        # Generate summary from content
        content_preview = blog_result.content[:300] + "..." if len(blog_result.content) > 300 else blog_result.content
        
        return {
            "content": html_content,
            "summary": content_preview,
            "seo_title": seo_data.get("title", blog_result.title),
            "seo_description": seo_data.get("description", content_preview)
        }
    
    async def _resolve_categories(self, categories: List[str]) -> List[int]:
        """Resolve category names to IDs, creating them if necessary."""
        category_ids = []
        
        # Get existing categories
        existing_categories = await self.get_categories()
        category_map = {cat["name"].lower(): cat["id"] for cat in existing_categories}
        
        for category_name in categories:
            category_lower = category_name.lower()
            
            if category_lower in category_map:
                category_ids.append(category_map[category_lower])
            else:
                # Create new category
                try:
                    new_category = await self.create_category(category_name)
                    category_ids.append(new_category["id"])
                    category_map[category_lower] = new_category["id"]
                except Exception as e:
                    self.logger.warning(f"Failed to create category '{category_name}': {str(e)}")
        
        return category_ids
    
    async def _resolve_tags(self, tags: List[str]) -> List[int]:
        """Resolve tag names to IDs, creating them if necessary."""
        tag_ids = []
        
        # Get existing tags
        existing_tags = await self.get_tags()
        tag_map = {tag["name"].lower(): tag["id"] for tag in existing_tags}
        
        for tag_name in tags:
            tag_lower = tag_name.lower()
            
            if tag_lower in tag_map:
                tag_ids.append(tag_map[tag_lower])
            else:
                # Create new tag
                try:
                    new_tag = await self.create_tag(tag_name)
                    tag_ids.append(new_tag["id"])
                    tag_map[tag_lower] = new_tag["id"]
                except Exception as e:
                    self.logger.warning(f"Failed to create tag '{tag_name}': {str(e)}")
        
        return tag_ids
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type based on file extension."""
        ext = filename.lower().split('.')[-1]
        content_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'svg': 'image/svg+xml',
            'mp4': 'video/mp4',
            'webm': 'video/webm',
            'pdf': 'application/pdf'
        }
        return content_types.get(ext, 'application/octet-stream')
    
    def _markdown_to_html(self, markdown_content: str) -> str:
        """Convert basic markdown to HTML."""
        import re
        
        html = markdown_content
        
        # Headers
        html = re.sub(r'^# (.*)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.*)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^#### (.*)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
        
        # Bold and italic
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
        
        # Links
        html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
        
        # Lists
        html = re.sub(r'^\* (.*)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'(\n<li>.*</li>)', r'\n<ul>\1\n</ul>', html, flags=re.DOTALL)
        
        # Line breaks
        html = html.replace('\n\n', '</p><p>')
        html = f'<p>{html}</p>'
        
        return html


class WordPressPublisher:
    """
    High-level publisher for WordPress integration.
    
    Provides convenient methods for publishing blog content to WordPress
    with automatic category/tag management and media handling.
    """
    
    def __init__(self, wordpress_client: Optional[WordPressClient] = None):
        """
        Initialize WordPress publisher.
        
        Args:
            wordpress_client: WordPress client instance
        """
        self.wordpress_client = wordpress_client or WordPressClient()
        self.logger = logging.getLogger(__name__)
    
    async def publish_with_media(
        self,
        blog_result: BlogGenerationResult,
        media_files: Optional[List[Dict[str, Any]]] = None,
        categories: Optional[List[str]] = None,
        status: str = "publish",
        publish: bool = True
    ) -> Dict[str, Any]:
        """
        Publish blog post with associated media files.
        
        Args:
            blog_result: Generated blog content
            media_files: List of media files to upload
            categories: List of categories
            status: Post status
            publish: Whether to publish immediately
            
        Returns:
            Dictionary containing publication details
        """
        try:
            uploaded_media = []
            featured_media_id = None
            
            # Upload media files if provided
            if media_files:
                for i, media_file in enumerate(media_files):
                    media_result = await self.wordpress_client.upload_media(
                        media_data=media_file["data"],
                        filename=media_file["filename"],
                        alt_text=media_file.get("alt_text"),
                        caption=media_file.get("caption")
                    )
                    uploaded_media.append(media_result)
                    
                    # Set first image as featured media
                    if i == 0 and media_result.get("type") == "image":
                        featured_media_id = media_result["id"]
            
            # Publish the blog post
            result = await self.wordpress_client.publish_blog_post(
                blog_result=blog_result,
                status=status if publish else "draft",
                categories=categories,
                featured_media=featured_media_id
            )
            
            result["uploaded_media"] = uploaded_media
            
            self.logger.info(f"Successfully published blog to WordPress with {len(uploaded_media)} media files")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to publish blog with media to WordPress: {str(e)}")
            raise
