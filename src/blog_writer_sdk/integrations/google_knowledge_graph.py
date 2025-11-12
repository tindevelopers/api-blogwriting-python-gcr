"""
Google Knowledge Graph API Integration

Provides entity recognition, structured data generation, and semantic understanding
using Google Knowledge Graph API.
"""

import os
import asyncio
import aiohttp
from typing import List, Dict, Optional, Any
from urllib.parse import quote_plus
import logging

logger = logging.getLogger(__name__)


class GoogleKnowledgeGraphClient:
    """Client for Google Knowledge Graph API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Google Knowledge Graph client.
        
        Args:
            api_key: Google Knowledge Graph API key (or from GOOGLE_KNOWLEDGE_GRAPH_API_KEY env)
        """
        self.api_key = api_key or os.getenv("GOOGLE_KNOWLEDGE_GRAPH_API_KEY")
        self.base_url = "https://kgsearch.googleapis.com/v1/entities:search"
        self.session: Optional[aiohttp.ClientSession] = None
        
        if not self.api_key:
            logger.warning("Google Knowledge Graph API key not configured")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def search_entities(
        self,
        query: str,
        limit: int = 10,
        languages: List[str] = None,
        types: List[str] = None,
        indent: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for entities in Knowledge Graph.
        
        Args:
            query: Search query
            limit: Maximum number of results
            languages: Language codes (e.g., ['en'])
            types: Entity types to filter (e.g., ['Person', 'Organization'])
            indent: Whether to indent JSON response
        
        Returns:
            List of entity results
        """
        if not self.api_key:
            logger.warning("Knowledge Graph API key not configured")
            return []
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        params = {
            "query": query,
            "key": self.api_key,
            "limit": min(limit, 20),  # API max is 20
            "indent": str(indent).lower()
        }
        
        if languages:
            params["languages"] = ",".join(languages)
        if types:
            params["types"] = ",".join(types)
        
        try:
            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    items = data.get("itemListElement", [])
                    
                    entities = []
                    for item in items:
                        result = item.get("result", {})
                        entity = {
                            "name": result.get("name", ""),
                            "description": result.get("description", ""),
                            "detailed_description": result.get("detailedDescription", {}),
                            "url": result.get("url", ""),
                            "image": result.get("image", {}),
                            "types": result.get("@type", []),
                            "score": item.get("resultScore", 0)
                        }
                        entities.append(entity)
                    
                    return entities[:limit]
                else:
                    error_text = await response.text()
                    logger.error(f"Knowledge Graph API error: {response.status} - {error_text}")
                    return []
        except Exception as e:
            logger.error(f"Error querying Knowledge Graph: {e}")
            return []
    
    async def get_entity_details(
        self,
        entity_name: str,
        language: str = "en"
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific entity.
        
        Args:
            entity_name: Name of the entity
            language: Language code
        
        Returns:
            Entity details or None
        """
        entities = await self.search_entities(
            query=entity_name,
            limit=1,
            languages=[language]
        )
        
        if entities:
            return entities[0]
        return None
    
    async def extract_entities_from_content(
        self,
        content: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Extract entities mentioned in content.
        
        Args:
            content: Content to analyze
            limit: Maximum number of entities to extract
        
        Returns:
            List of extracted entities
        """
        # Simple extraction: look for capitalized phrases
        # In production, could use NLP for better extraction
        import re
        potential_entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
        
        unique_entities = list(set(potential_entities))[:limit]
        
        extracted = []
        for entity_name in unique_entities:
            if len(entity_name.split()) <= 3:  # Limit to reasonable entity names
                entity_details = await self.get_entity_details(entity_name)
                if entity_details:
                    extracted.append(entity_details)
        
        return extracted
    
    def generate_schema_markup(
        self,
        entity: Dict[str, Any],
        content_type: str = "Article"
    ) -> Dict[str, Any]:
        """
        Generate schema.org JSON-LD markup from entity.
        
        Args:
            entity: Entity information from Knowledge Graph
            content_type: Type of schema (Article, BlogPosting, etc.)
        
        Returns:
            Schema.org JSON-LD structure
        """
        schema = {
            "@context": "https://schema.org",
            "@type": content_type
        }
        
        if entity.get("name"):
            schema["about"] = {
                "@type": "Thing",
                "name": entity["name"]
            }
        
        if entity.get("description"):
            schema["description"] = entity["description"]
        
        if entity.get("url"):
            schema["url"] = entity["url"]
        
        if entity.get("image", {}).get("contentUrl"):
            schema["image"] = entity["image"]["contentUrl"]
        
        # Add entity-specific properties
        entity_types = entity.get("types", [])
        if "Person" in entity_types:
            schema["author"] = {
                "@type": "Person",
                "name": entity["name"]
            }
        elif "Organization" in entity_types:
            schema["publisher"] = {
                "@type": "Organization",
                "name": entity["name"]
            }
        
        return schema
    
    async def generate_structured_data(
        self,
        topic: str,
        content: str,
        keywords: List[str]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive structured data for content.
        
        Args:
            topic: Main topic
            content: Content body
            keywords: Related keywords
        
        Returns:
            Complete structured data schema
        """
        # Get main entity
        main_entity = await self.get_entity_details(topic)
        
        # Extract related entities
        related_entities = await self.extract_entities_from_content(content, limit=5)
        
        # Build comprehensive schema
        schema = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": topic,
            "keywords": ", ".join(keywords)
        }
        
        if main_entity:
            schema["about"] = {
                "@type": "Thing",
                "name": main_entity.get("name", topic),
                "description": main_entity.get("description", "")
            }
        
        if related_entities:
            schema["mentions"] = [
                {
                    "@type": "Thing",
                    "name": e.get("name", "")
                }
                for e in related_entities[:3]
            ]
        
        return schema

