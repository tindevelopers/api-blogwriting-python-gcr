"""
Supabase integration for the Blog Writer SDK with multi-environment support.

This module provides database operations for storing and managing
blog posts, analytics, and user data using Supabase with environment-specific
table isolation (dev/staging/prod).
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None

from ..models.blog_models import BlogPost, BlogGenerationResult


class SupabaseClient:
    """
    Supabase client for blog writer operations with multi-environment support.
    
    Handles database operations for blog posts, analytics,
    and content management using Supabase with environment-specific table isolation.
    """
    
    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        environment: Optional[str] = None,
    ):
        """
        Initialize Supabase client with environment support.
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase service role key
            environment: Environment name (dev/staging/prod)
        """
        if not create_client:
            raise ImportError("supabase package is required for database integration")
        
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.environment = environment or os.getenv("ENVIRONMENT", "dev")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and key are required")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        self.logger = logging.getLogger(__name__)
    
    def _get_table_name(self, base_name: str) -> str:
        """
        Get environment-specific table name.
        
        Args:
            base_name: Base table name (e.g., 'blog_posts')
            
        Returns:
            Environment-specific table name (e.g., 'blog_posts_prod')
        """
        return f"{base_name}_{self.environment}"
    
    async def save_blog_post(self, blog_post: BlogPost, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Save a blog post to the database.
        
        Args:
            blog_post: Blog post object to save
            user_id: Optional user ID for association
            
        Returns:
            Database record of the saved blog post
        """
        try:
            # Prepare blog post data
            post_data = {
                "title": blog_post.title,
                "content": blog_post.content,
                "excerpt": blog_post.excerpt,
                "slug": blog_post.slug,
                "author": blog_post.author,
                "categories": blog_post.categories or [],
                "tags": blog_post.tags or [],
                "status": blog_post.status,
                "featured_image": blog_post.featured_image,
                "meta_title": blog_post.meta_title,
                "meta_description": blog_post.meta_description,
                "meta_keywords": blog_post.meta_keywords or [],
                "canonical_url": blog_post.canonical_url,
                "og_title": blog_post.og_title,
                "og_description": blog_post.og_description,
                "og_image": blog_post.og_image,
                "twitter_title": blog_post.twitter_title,
                "twitter_description": blog_post.twitter_description,
                "seo_score": blog_post.seo_score,
                "word_count": blog_post.word_count,
                "reading_time": blog_post.reading_time,
                "keyword_density": blog_post.keyword_density,
                "seo_recommendations": blog_post.seo_recommendations or [],
                "readability_score": blog_post.readability_score,
                "flesch_reading_ease": blog_post.flesch_reading_ease,
                "flesch_kincaid_grade": blog_post.flesch_kincaid_grade,
                "updated_at": datetime.utcnow().isoformat(),
                "user_id": user_id
            }
            
            # Add published_at if status is published
            if blog_post.status == "published" and not post_data.get("published_at"):
                post_data["published_at"] = datetime.utcnow().isoformat()
            
            table_name = self._get_table_name("blog_posts")
            result = self.client.table(table_name).insert(post_data).execute()
            
            if result.data:
                self.logger.info(f"Blog post saved successfully: {result.data[0]['id']}")
                return result.data[0]
            else:
                raise Exception("Failed to save blog post")
                
        except Exception as e:
            self.logger.error(f"Error saving blog post: {str(e)}")
            raise
    
    async def get_blog_post(self, post_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve a blog post by ID.
        
        Args:
            post_id: Blog post ID
            user_id: Optional user ID for filtering
            
        Returns:
            Blog post data or None if not found
        """
        try:
            table_name = self._get_table_name("blog_posts")
            query = self.client.table(table_name).select("*").eq("id", post_id)
            
            if user_id:
                query = query.eq("user_id", user_id)
            
            result = query.execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving blog post: {str(e)}")
            raise
    
    async def list_blog_posts(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List blog posts with optional filtering.
        
        Args:
            user_id: Optional user ID for filtering
            status: Optional status filter
            limit: Maximum number of posts to return
            offset: Number of posts to skip
            
        Returns:
            List of blog post data
        """
        try:
            table_name = self._get_table_name("blog_posts")
            query = self.client.table(table_name).select("*")
            
            if user_id:
                query = query.eq("user_id", user_id)
            if status:
                query = query.eq("status", status)
            
            query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
            result = query.execute()
            
            return result.data or []
            
        except Exception as e:
            self.logger.error(f"Error listing blog posts: {str(e)}")
            raise
    
    async def update_blog_post(
        self,
        post_id: str,
        updates: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update a blog post.
        
        Args:
            post_id: Blog post ID
            updates: Dictionary of fields to update
            user_id: Optional user ID for filtering
            
        Returns:
            Updated blog post data
        """
        try:
            # Add updated timestamp
            updates["updated_at"] = datetime.utcnow().isoformat()
            
            table_name = self._get_table_name("blog_posts")
            query = self.client.table(table_name).update(updates).eq("id", post_id)
            
            if user_id:
                query = query.eq("user_id", user_id)
            
            result = query.execute()
            
            if result.data:
                self.logger.info(f"Blog post updated successfully: {post_id}")
                return result.data[0]
            else:
                raise Exception("Failed to update blog post")
                
        except Exception as e:
            self.logger.error(f"Error updating blog post: {str(e)}")
            raise
    
    async def delete_blog_post(self, post_id: str, user_id: Optional[str] = None) -> bool:
        """
        Delete a blog post.
        
        Args:
            post_id: Blog post ID
            user_id: Optional user ID for filtering
            
        Returns:
            True if deleted successfully
        """
        try:
            table_name = self._get_table_name("blog_posts")
            query = self.client.table(table_name).delete().eq("id", post_id)
            
            if user_id:
                query = query.eq("user_id", user_id)
            
            result = query.execute()
            
            if result.data:
                self.logger.info(f"Blog post deleted successfully: {post_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error deleting blog post: {str(e)}")
            raise
    
    async def log_generation_analytics(
        self,
        topic: str,
        success: bool,
        word_count: Optional[int] = None,
        generation_time: Optional[float] = None,
        seo_score: Optional[float] = None,
        readability_score: Optional[float] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Log blog generation analytics.
        
        Args:
            topic: Blog topic
            success: Whether generation was successful
            word_count: Number of words generated
            generation_time: Time taken for generation
            seo_score: SEO score of generated content
            readability_score: Readability score of generated content
            user_id: Optional user ID
            
        Returns:
            Analytics record
        """
        try:
            analytics_data = {
                "topic": topic,
                "success": success,
                "word_count": word_count,
                "generation_time": generation_time,
                "seo_score": seo_score,
                "readability_score": readability_score,
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat()
            }
            
            table_name = self._get_table_name("generation_analytics")
            result = self.client.table(table_name).insert(analytics_data).execute()
            
            if result.data:
                return result.data[0]
            else:
                raise Exception("Failed to log analytics")
                
        except Exception as e:
            self.logger.error(f"Error logging analytics: {str(e)}")
            raise
    
    async def get_analytics_summary(
        self,
        user_id: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get analytics summary.
        
        Args:
            user_id: Optional user ID for filtering
            days: Number of days to look back
            
        Returns:
            Analytics summary
        """
        try:
            # Calculate date threshold
            from datetime import timedelta
            threshold_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            table_name = self._get_table_name("generation_analytics")
            query = self.client.table(table_name).select("*").gte("created_at", threshold_date)
            
            if user_id:
                query = query.eq("user_id", user_id)
            
            result = query.execute()
            data = result.data or []
            
            # Calculate summary statistics
            total_generations = len(data)
            successful_generations = len([d for d in data if d.get("success", False)])
            avg_generation_time = sum(d.get("generation_time", 0) for d in data if d.get("generation_time")) / max(1, len([d for d in data if d.get("generation_time")]))
            avg_seo_score = sum(d.get("seo_score", 0) for d in data if d.get("seo_score")) / max(1, len([d for d in data if d.get("seo_score")]))
            avg_readability_score = sum(d.get("readability_score", 0) for d in data if d.get("readability_score")) / max(1, len([d for d in data if d.get("readability_score")]))
            
            return {
                "total_generations": total_generations,
                "successful_generations": successful_generations,
                "success_rate": successful_generations / max(1, total_generations),
                "average_generation_time": avg_generation_time,
                "average_seo_score": avg_seo_score,
                "average_readability_score": avg_readability_score,
                "period_days": days
            }
            
        except Exception as e:
            self.logger.error(f"Error getting analytics summary: {str(e)}")
            raise
    
    async def search_blog_posts(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Search blog posts by content.
        
        Args:
            query: Search query
            user_id: Optional user ID for filtering
            limit: Maximum number of results
            
        Returns:
            List of matching blog posts
        """
        try:
            # Use Supabase full-text search if available
            table_name = self._get_table_name("blog_posts")
            search_query = self.client.table(table_name).select("*")
            
            if user_id:
                search_query = search_query.eq("user_id", user_id)
            
            # Simple text search (can be enhanced with full-text search)
            search_query = search_query.or_(f"title.ilike.%{query}%,content.ilike.%{query}%")
            search_query = search_query.limit(limit)
            
            result = search_query.execute()
            return result.data or []
            
        except Exception as e:
            self.logger.error(f"Error searching blog posts: {str(e)}")
            raise
    
    def create_database_schema(self, create_all_environments: bool = True) -> str:
        """
        Generate SQL schema for the required database tables.
        
        Args:
            create_all_environments: If True, creates tables for all environments
            
        Returns:
            SQL schema as string
        """
        environments = ["dev", "staging", "prod"] if create_all_environments else [self.environment]
        
        schema_parts = []
        
        for env in environments:
            schema_parts.append(f"""
-- Blog posts table for {env} environment
CREATE TABLE IF NOT EXISTS blog_posts_{env} (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    excerpt TEXT,
    slug TEXT NOT NULL,
    author TEXT,
    categories TEXT[] DEFAULT '{{}}',
    tags TEXT[] DEFAULT '{{}}',
    status TEXT DEFAULT 'draft',
    featured_image TEXT,
    
    -- Meta tags
    meta_title TEXT,
    meta_description TEXT,
    meta_keywords TEXT[],
    canonical_url TEXT,
    og_title TEXT,
    og_description TEXT,
    og_image TEXT,
    twitter_title TEXT,
    twitter_description TEXT,
    
    -- SEO metrics
    seo_score DECIMAL(5,2),
    word_count INTEGER,
    reading_time DECIMAL(5,2),
    keyword_density JSONB,
    seo_recommendations TEXT[],
    
    -- Content quality
    readability_score DECIMAL(5,2),
    flesch_reading_ease DECIMAL(5,2),
    flesch_kincaid_grade DECIMAL(5,2),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    published_at TIMESTAMPTZ,
    
    -- User association
    user_id UUID,
    
    UNIQUE(slug)
);

-- Generation analytics table for {env} environment
CREATE TABLE IF NOT EXISTS generation_analytics_{env} (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    topic TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    word_count INTEGER,
    generation_time DECIMAL(8,3),
    seo_score DECIMAL(5,2),
    readability_score DECIMAL(5,2),
    user_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance ({env} environment)
CREATE INDEX IF NOT EXISTS idx_blog_posts_{env}_user_id ON blog_posts_{env}(user_id);
CREATE INDEX IF NOT EXISTS idx_blog_posts_{env}_status ON blog_posts_{env}(status);
CREATE INDEX IF NOT EXISTS idx_blog_posts_{env}_created_at ON blog_posts_{env}(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_blog_posts_{env}_slug ON blog_posts_{env}(slug);
CREATE INDEX IF NOT EXISTS idx_generation_analytics_{env}_user_id ON generation_analytics_{env}(user_id);
CREATE INDEX IF NOT EXISTS idx_generation_analytics_{env}_created_at ON generation_analytics_{env}(created_at DESC);

-- Full-text search indexes ({env} environment)
CREATE INDEX IF NOT EXISTS idx_blog_posts_{env}_title_search ON blog_posts_{env} USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_blog_posts_{env}_content_search ON blog_posts_{env} USING gin(to_tsvector('english', content));

-- Row Level Security (RLS) policies ({env} environment)
ALTER TABLE blog_posts_{env} ENABLE ROW LEVEL SECURITY;
ALTER TABLE generation_analytics_{env} ENABLE ROW LEVEL SECURITY;

-- Policies for blog_posts_{env} (users can only access their own posts)
CREATE POLICY "Users can view their own blog posts {env}" ON blog_posts_{env}
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own blog posts {env}" ON blog_posts_{env}
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own blog posts {env}" ON blog_posts_{env}
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own blog posts {env}" ON blog_posts_{env}
    FOR DELETE USING (auth.uid() = user_id);

-- Policies for generation_analytics_{env}
CREATE POLICY "Users can view their own analytics {env}" ON generation_analytics_{env}
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own analytics {env}" ON generation_analytics_{env}
    FOR INSERT WITH CHECK (auth.uid() = user_id);
""")
        
        return "\n".join(schema_parts)