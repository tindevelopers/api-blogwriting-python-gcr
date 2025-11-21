"""
Shopify integration for the Blog Writer SDK.

This module provides integration with Shopify for publishing blog posts
to the Shopify blog system and managing associated products.
"""

import os
import logging
import httpx
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import json
import hashlib

from ..models.blog_models import BlogPost, BlogGenerationResult


class ShopifyClient:
    """
    Shopify client for blog writer operations.
    
    Handles publishing blog posts to Shopify blogs, managing articles,
    and integrating with product catalogs.
    """
    
    def __init__(
        self,
        shop_domain: Optional[str] = None,
        access_token: Optional[str] = None,
        blog_id: Optional[str] = None,
    ):
        """
        Initialize Shopify client.
        
        Args:
            shop_domain: Shopify shop domain (e.g., 'your-shop.myshopify.com')
            access_token: Shopify private app access token
            blog_id: Default blog ID for publishing
        """
        self.shop_domain = shop_domain or os.getenv("SHOPIFY_SHOP_DOMAIN")
        self.access_token = access_token or os.getenv("SHOPIFY_ACCESS_TOKEN")
        self.blog_id = blog_id or os.getenv("SHOPIFY_BLOG_ID")
        
        if not self.shop_domain or not self.access_token:
            raise ValueError("Shopify shop domain and access token are required")
        
        # Ensure shop domain has proper format
        if not self.shop_domain.endswith('.myshopify.com'):
            if not self.shop_domain.startswith('http'):
                self.shop_domain = f"https://{self.shop_domain}.myshopify.com"
            else:
                self.shop_domain = self.shop_domain.replace('https://', '').replace('http://', '')
                if not self.shop_domain.endswith('.myshopify.com'):
                    self.shop_domain = f"{self.shop_domain}.myshopify.com"
                self.shop_domain = f"https://{self.shop_domain}"
        
        self.base_url = f"{self.shop_domain}/admin/api/2023-10"
        self.headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.logger = logging.getLogger(__name__)
    
    async def publish_blog_post(
        self, 
        blog_result: BlogGenerationResult,
        blog_id: Optional[str] = None,
        published: bool = True,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Publish a blog post to Shopify.
        
        Args:
            blog_result: Generated blog content
            blog_id: Target blog ID (overrides instance setting)
            published: Whether to publish immediately
            tags: Additional tags for the article
            
        Returns:
            Dictionary containing Shopify article details
        """
        target_blog_id = blog_id or self.blog_id
        
        if not target_blog_id:
            raise ValueError("Shopify blog ID is required")
        
        try:
            # Prepare content for Shopify
            shopify_content = await self._prepare_shopify_content(blog_result)
            
            # Create the article
            article_data = {
                "article": {
                    "title": blog_result.title,
                    "body_html": shopify_content["content_html"],
                    "summary": shopify_content["summary"],
                    "author": shopify_content.get("author", "AI Content Generator"),
                    "blog_id": target_blog_id,
                    "published": published,
                    "tags": ",".join((blog_result.keywords or []) + (tags or [])),
                    "handle": self._generate_handle(blog_result.title),
                    "seo_title": shopify_content.get("seo_title", blog_result.title),
                    "seo_description": shopify_content.get("seo_description", shopify_content["summary"]),
                    "created_at": datetime.now().isoformat()
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/blogs/{target_blog_id}/articles.json",
                    headers=self.headers,
                    json=article_data,
                    timeout=30.0
                )
                response.raise_for_status()
                
                article_result = response.json()
                
                self.logger.info(f"Created Shopify article: {article_result['article']['id']}")
                
                return article_result
                
        except Exception as e:
            self.logger.error(f"Failed to publish to Shopify: {str(e)}")
            raise
    
    async def upload_media(
        self, 
        media_data: bytes, 
        filename: str,
        alt_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload media to Shopify.
        
        Args:
            media_data: Media file data
            filename: Original filename
            alt_text: Alt text for the media
            
        Returns:
            Dictionary containing media upload details
        """
        try:
            # Create base64 encoded data for Shopify
            media_base64 = base64.b64encode(media_data).decode('utf-8')
            
            # Upload to Shopify assets
            async with httpx.AsyncClient() as client:
                upload_data = {
                    "asset": {
                        "key": f"assets/{filename}",
                        "value": media_base64,
                        "content_type": self._get_content_type(filename)
                    }
                }
                
                response = await client.put(
                    f"{self.base_url}/themes/{await self._get_current_theme_id()}/assets.json",
                    headers=self.headers,
                    json=upload_data,
                    timeout=60.0
                )
                response.raise_for_status()
                
                asset_result = response.json()
                
                # Get the public URL
                public_url = f"{self.shop_domain}/cdn/shop/files/{filename}"
                
                result = {
                    "id": asset_result["asset"]["key"],
                    "url": public_url,
                    "filename": filename,
                    "alt_text": alt_text,
                    "content_type": self._get_content_type(filename)
                }
                
                self.logger.info(f"Uploaded media to Shopify: {result['id']}")
                
                return result
                
        except Exception as e:
            self.logger.error(f"Failed to upload media to Shopify: {str(e)}")
            raise
    
    async def get_blogs(self) -> List[Dict[str, Any]]:
        """
        Get all blogs for the shop.
        
        Returns:
            List of blog details
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/blogs.json",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                
                blogs = response.json()
                return blogs.get("blogs", [])
                
        except Exception as e:
            self.logger.error(f"Failed to get Shopify blogs: {str(e)}")
            raise
    
    async def get_articles(
        self, 
        blog_id: Optional[str] = None,
        limit: int = 250
    ) -> List[Dict[str, Any]]:
        """
        Get articles from a blog.
        
        Args:
            blog_id: Blog ID (uses default if not provided)
            limit: Maximum number of articles to retrieve
            
        Returns:
            List of articles
        """
        target_blog_id = blog_id or self.blog_id
        
        if not target_blog_id:
            raise ValueError("Shopify blog ID is required")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/blogs/{target_blog_id}/articles.json",
                    headers=self.headers,
                    params={"limit": limit},
                    timeout=30.0
                )
                response.raise_for_status()
                
                articles = response.json()
                return articles.get("articles", [])
                
        except Exception as e:
            self.logger.error(f"Failed to get Shopify articles: {str(e)}")
            raise
    
    async def search_products(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search products in the shop for content integration.
        
        Args:
            query: Search query
            limit: Maximum number of products to return
            
        Returns:
            List of matching products
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/products.json",
                    headers=self.headers,
                    params={
                        "title": query,
                        "limit": limit,
                        "published_status": "published"
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                
                products = response.json()
                return products.get("products", [])
                
        except Exception as e:
            self.logger.error(f"Failed to search Shopify products: {str(e)}")
            raise
    
    async def create_product_recommendations(
        self,
        blog_result: BlogGenerationResult,
        max_products: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Create product recommendations based on blog content.
        
        Args:
            blog_result: Generated blog content
            max_products: Maximum number of product recommendations
            
        Returns:
            List of recommended products
        """
        try:
            recommendations = []
            
            # Extract keywords for product search
            search_keywords = blog_result.keywords or []
            if blog_result.focus_keyword:
                search_keywords.insert(0, blog_result.focus_keyword)
            
            # Search for products based on keywords
            for keyword in search_keywords[:3]:  # Limit to top 3 keywords
                products = await self.search_products(keyword, limit=5)
                
                for product in products[:2]:  # Take top 2 products per keyword
                    if len(recommendations) >= max_products:
                        break
                    
                    # Avoid duplicates
                    if not any(rec["id"] == product["id"] for rec in recommendations):
                        recommendations.append({
                            "id": product["id"],
                            "title": product["title"],
                            "handle": product["handle"],
                            "url": f"{self.shop_domain}/products/{product['handle']}",
                            "price": product.get("variants", [{}])[0].get("price", "0"),
                            "image": product.get("image", {}).get("src", ""),
                            "description": product.get("body_html", ""),
                            "tags": product.get("tags", "").split(",") if product.get("tags") else [],
                            "relevance_score": self._calculate_relevance_score(product, search_keywords)
                        })
                
                if len(recommendations) >= max_products:
                    break
            
            # Sort by relevance score
            recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            return recommendations[:max_products]
            
        except Exception as e:
            self.logger.error(f"Failed to create product recommendations: {str(e)}")
            return []
    
    async def _prepare_shopify_content(self, blog_result: BlogGenerationResult) -> Dict[str, Any]:
        """Prepare blog content for Shopify format."""
        
        # Convert markdown to HTML (basic conversion)
        html_content = self._markdown_to_html(blog_result.content)
        
        # Extract SEO data
        seo_data = blog_result.seo_data or {}
        
        # Generate summary from content
        content_preview = blog_result.content[:300] + "..." if len(blog_result.content) > 300 else blog_result.content
        
        return {
            "content_html": html_content,
            "summary": content_preview,
            "seo_title": seo_data.get("title", blog_result.title),
            "seo_description": seo_data.get("description", content_preview),
            "author": "AI Content Generator"
        }
    
    def _generate_handle(self, title: str) -> str:
        """Generate URL-friendly handle from title."""
        import re
        
        # Convert to lowercase and replace spaces with hyphens
        handle = title.lower()
        handle = re.sub(r'[^\w\s-]', '', handle)  # Remove special characters
        handle = re.sub(r'[-\s]+', '-', handle)   # Replace spaces and multiple hyphens
        handle = handle.strip('-')                # Remove leading/trailing hyphens
        
        # Add timestamp to ensure uniqueness
        timestamp = datetime.now().strftime("%Y%m%d")
        return f"{handle}-{timestamp}"
    
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
    
    async def _get_current_theme_id(self) -> str:
        """Get the current active theme ID."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/themes.json",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                
                themes = response.json()
                
                # Find the published theme
                for theme in themes.get("themes", []):
                    if theme.get("role") == "main":
                        return theme["id"]
                
                # Fallback to first theme
                if themes.get("themes"):
                    return themes["themes"][0]["id"]
                
                raise ValueError("No themes found")
                
        except Exception as e:
            self.logger.error(f"Failed to get current theme ID: {str(e)}")
            raise
    
    def _markdown_to_html(self, markdown_content: str) -> str:
        """Convert basic markdown to HTML."""
        import re
        
        html = markdown_content
        
        # Headers
        html = re.sub(r'^# (.*)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.*)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        
        # Bold and italic
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
        
        # Links
        html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
        
        # Line breaks
        html = html.replace('\n', '<br>\n')
        
        return html
    
    def _calculate_relevance_score(self, product: Dict[str, Any], keywords: List[str]) -> float:
        """Calculate relevance score for product recommendations."""
        score = 0.0
        
        # Check title match
        title_lower = product.get("title", "").lower()
        for keyword in keywords:
            if keyword.lower() in title_lower:
                score += 2.0
        
        # Check tags match
        tags = product.get("tags", "").lower()
        for keyword in keywords:
            if keyword.lower() in tags:
                score += 1.0
        
        # Check description match
        description = product.get("body_html", "").lower()
        for keyword in keywords:
            if keyword.lower() in description:
                score += 0.5
        
        return score


class ShopifyPublisher:
    """
    High-level publisher for Shopify integration.
    
    Provides convenient methods for publishing blog content to Shopify
    with automatic product recommendations and media handling.
    """
    
    def __init__(self, shopify_client: Optional[ShopifyClient] = None):
        """
        Initialize Shopify publisher.
        
        Args:
            shopify_client: Shopify client instance
        """
        self.shopify_client = shopify_client or ShopifyClient()
        self.logger = logging.getLogger(__name__)
    
    async def publish_with_recommendations(
        self,
        blog_result: BlogGenerationResult,
        blog_id: Optional[str] = None,
        include_products: bool = True,
        max_products: int = 3,
        publish: bool = True
    ) -> Dict[str, Any]:
        """
        Publish blog post with product recommendations.
        
        Args:
            blog_result: Generated blog content
            blog_id: Target blog ID
            include_products: Whether to include product recommendations
            max_products: Maximum number of product recommendations
            publish: Whether to publish immediately
            
        Returns:
            Dictionary containing publication details
        """
        try:
            # Create product recommendations if requested
            recommendations = []
            if include_products:
                recommendations = await self.shopify_client.create_product_recommendations(
                    blog_result, max_products
                )
            
            # Publish the blog post
            result = await self.shopify_client.publish_blog_post(
                blog_result=blog_result,
                blog_id=blog_id,
                published=publish
            )
            
            result["product_recommendations"] = recommendations
            
            self.logger.info(f"Successfully published blog to Shopify with {len(recommendations)} product recommendations")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to publish blog with recommendations to Shopify: {str(e)}")
            raise

