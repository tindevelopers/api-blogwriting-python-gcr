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
        self.environment = environment or os.getenv("DATABASE_ENVIRONMENT", "dev")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and service role key are required")
        
        # Validate environment
        if self.environment not in ["dev", "staging", "prod"]:
            raise ValueError(f"Invalid environment: {self.environment}. Must be dev, staging, or prod.")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initialized Supabase client for environment: {self.environment}")
    
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
            blog_post: BlogPost object to save
            user_id: Optional user ID for ownership
            
        Returns:
            Database record of the saved blog post
        """
        try:
            # Prepare blog post data
            blog_data = {
                "title": blog_post.title,
                "content": blog_post.content,
                "excerpt": blog_post.excerpt,
                "slug": blog_post.slug,
                "author": blog_post.author,
                "categories": blog_post.categories,
                "tags": blog_post.tags,
                "status": blog_post.status,
                "featured_image": str(blog_post.featured_image) if blog_post.featured_image else None,
                "created_at": blog_post.created_at.isoformat(),
                "updated_at": blog_post.updated_at.isoformat() if blog_post.updated_at else None,
                "published_at": blog_post.published_at.isoformat() if blog_post.published_at else None,
                "user_id": user_id,
            }
            
            # Add meta tags
            if blog_post.meta_tags:
                blog_data["meta_title"] = blog_post.meta_tags.title
                blog_data["meta_description"] = blog_post.meta_tags.description
                blog_data["meta_keywords"] = blog_post.meta_tags.keywords
                blog_data["canonical_url"] = str(blog_post.meta_tags.canonical_url) if blog_post.meta_tags.canonical_url else None
                blog_data["og_title"] = blog_post.meta_tags.og_title
                blog_data["og_description"] = blog_post.meta_tags.og_description
                blog_data["og_image"] = str(blog_post.meta_tags.og_image) if blog_post.meta_tags.og_image else None
                blog_data["twitter_title"] = blog_post.meta_tags.twitter_title
                blog_data["twitter_description"] = blog_post.meta_tags.twitter_description
            
            # Add SEO metrics
            if blog_post.seo_metrics:
                blog_data["seo_score"] = blog_post.seo_metrics.overall_seo_score
                blog_data["word_count"] = blog_post.seo_metrics.word_count
                blog_data["reading_time"] = blog_post.seo_metrics.reading_time_minutes
                blog_data["keyword_density"] = json.dumps(blog_post.seo_metrics.keyword_density)
                blog_data["seo_recommendations"] = blog_post.seo_metrics.recommendations
            
            # Add content quality metrics
            if blog_post.content_quality:
                blog_data["readability_score"] = blog_post.content_quality.readability_score
                blog_data["flesch_reading_ease"] = blog_post.content_quality.flesch_reading_ease
                blog_data["flesch_kincaid_grade"] = blog_post.content_quality.flesch_kincaid_grade
            
            # Insert into environment-specific table
            table_name = self._get_table_name("blog_posts")
            result = self.client.table(table_name).insert(blog_data).execute()
            
            if result.data:
                return result.data[0]
            else:
                raise Exception("Failed to save blog post")
                
        except Exception as e:
            raise Exception(f"Error saving blog post: {str(e)}")
    
    async def get_blog_post(self, post_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve a blog post by ID.
        
        Args:
            post_id: Blog post ID
            user_id: Optional user ID for ownership check
            
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
            raise Exception(f"Error retrieving blog post: {str(e)}")
    
    async def list_blog_posts(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List blog posts with optional filtering.
        
        Args:
            user_id: Optional user ID filter
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
            
            query = query.order("created_at", desc=True).limit(limit).offset(offset)
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            raise Exception(f"Error listing blog posts: {str(e)}")
    
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
            user_id: Optional user ID for ownership check
            
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
                return result.data[0]
            else:
                raise Exception("Blog post not found or update failed")
                
        except Exception as e:
            raise Exception(f"Error updating blog post: {str(e)}")
    
    async def delete_blog_post(self, post_id: str, user_id: Optional[str] = None) -> bool:
        """
        Delete a blog post.
        
        Args:
            post_id: Blog post ID
            user_id: Optional user ID for ownership check
            
        Returns:
            True if deleted successfully
        """
        try:
            table_name = self._get_table_name("blog_posts")
            query = self.client.table(table_name).delete().eq("id", post_id)
            
            if user_id:
                query = query.eq("user_id", user_id)
            
            result = query.execute()
            return len(result.data) > 0
            
        except Exception as e:
            raise Exception(f"Error deleting blog post: {str(e)}")
    
    async def log_generation(
        self,
        topic: str,
        success: bool,
        word_count: int,
        generation_time: float,
        user_id: Optional[str] = None,
        seo_score: Optional[float] = None,
        readability_score: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Log blog generation analytics.
        
        Args:
            topic: Blog topic
            success: Whether generation was successful
            word_count: Generated word count
            generation_time: Time taken to generate
            user_id: Optional user ID
            seo_score: Optional SEO score
            readability_score: Optional readability score
            
        Returns:
            Analytics record
        """
        try:
            analytics_data = {
                "topic": topic,
                "success": success,
                "word_count": word_count,
                "generation_time": generation_time,
                "user_id": user_id,
                "seo_score": seo_score,
                "readability_score": readability_score,
                "created_at": datetime.utcnow().isoformat(),
            }
            
            table_name = self._get_table_name("generation_analytics")
            result = self.client.table(table_name).insert(analytics_data).execute()
            
            if result.data:
                return result.data[0]
            else:
                raise Exception("Failed to log analytics")
                
        except Exception as e:
            raise Exception(f"Error logging analytics: {str(e)}")
    
    async def get_analytics(
        self,
        user_id: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get analytics summary.
        
        Args:
            user_id: Optional user ID filter
            days: Number of days to include
            
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
            analytics_data = result.data or []
            
            # Calculate summary statistics
            total_generations = len(analytics_data)
            successful_generations = sum(1 for record in analytics_data if record.get("success"))
            total_words = sum(record.get("word_count", 0) for record in analytics_data)
            avg_generation_time = sum(record.get("generation_time", 0) for record in analytics_data) / max(1, total_generations)
            avg_seo_score = sum(record.get("seo_score", 0) for record in analytics_data if record.get("seo_score")) / max(1, sum(1 for record in analytics_data if record.get("seo_score")))
            
            return {
                "period_days": days,
                "total_generations": total_generations,
                "successful_generations": successful_generations,
                "success_rate": successful_generations / max(1, total_generations),
                "total_words_generated": total_words,
                "average_generation_time": avg_generation_time,
                "average_seo_score": avg_seo_score,
                "recent_topics": [record.get("topic") for record in analytics_data[-10:]][::-1],  # Last 10, reversed
            }
            
        except Exception as e:
            raise Exception(f"Error retrieving analytics: {str(e)}")
    
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
            user_id: Optional user ID filter
            limit: Maximum results to return
            
        Returns:
            List of matching blog posts
        """
        try:
            # Use Supabase full-text search if available
            table_name = self._get_table_name("blog_posts")
            search_query = self.client.table(table_name).select("*")
            
            if user_id:
                search_query = search_query.eq("user_id", user_id)
            
            # Search in title and content
            search_query = search_query.or_(f"title.ilike.%{query}%,content.ilike.%{query}%")
            search_query = search_query.limit(limit)
            
            result = search_query.execute()
            return result.data or []
            
        except Exception as e:
            raise Exception(f"Error searching blog posts: {str(e)}")
    
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
    categories TEXT[] DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
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
