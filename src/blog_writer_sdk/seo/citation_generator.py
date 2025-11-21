"""
Citation and Source Integration

Automatically generates citations and integrates authoritative sources into content.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """Citation information."""
    text: str
    source_url: str
    source_title: str
    anchor_text: str
    position: int  # Character position in content


@dataclass
class CitationResult:
    """Result of citation generation."""
    citations: List[Citation]
    sources_used: List[Dict[str, str]]
    citation_count: int


class CitationGenerator:
    """Generates and integrates citations into content."""
    
    def __init__(self, google_search_client=None):
        """
        Initialize citation generator.
        
        Args:
            google_search_client: Google Custom Search client (optional)
        """
        self.google_search = google_search_client
    
    async def generate_citations(
        self,
        content: str,
        topic: str,
        keywords: List[str],
        num_citations: int = 5
    ) -> CitationResult:
        """
        Generate citations for content.
        
        Args:
            content: Content to add citations to
            topic: Main topic
            keywords: Related keywords
            num_citations: Number of citations to generate
        
        Returns:
            CitationResult with citations and sources
        """
        citations = []
        sources_used = []
        
        if not self.google_search:
            logger.warning("Google Search not available for citation generation")
            return CitationResult(
                citations=[],
                sources_used=[],
                citation_count=0
            )
        
        # Find authoritative sources
        try:
            sources = await self.google_search.search_for_sources(
                topic, keywords, num_results=num_citations
            )
            
            # Generate citations at natural points in content
            sentences = content.split('.')
            citation_points = self._identify_citation_points(sentences, len(sources))
            
            for i, (sentence_idx, source) in enumerate(zip(citation_points, sources)):
                citation = Citation(
                    text=sentences[sentence_idx] if sentence_idx < len(sentences) else "",
                    source_url=source.get('link', ''),
                    source_title=source.get('title', ''),
                    anchor_text=self._generate_anchor_text(source.get('title', '')),
                    position=len('. '.join(sentences[:sentence_idx])) if sentence_idx > 0 else 0
                )
                citations.append(citation)
                sources_used.append({
                    'url': source.get('link', ''),
                    'title': source.get('title', ''),
                    'snippet': source.get('snippet', '')
                })
        except Exception as e:
            logger.error(f"Citation generation failed: {e}")
        
        return CitationResult(
            citations=citations,
            sources_used=sources_used,
            citation_count=len(citations)
        )
    
    def integrate_citations(
        self,
        content: str,
        citations: List[Citation]
    ) -> str:
        """
        Integrate citations into content.
        
        Args:
            content: Original content
            citations: List of citations to integrate
        
        Returns:
            Content with citations integrated
        """
        # Sort citations by position (reverse to maintain positions when inserting)
        sorted_citations = sorted(citations, key=lambda x: x.position, reverse=True)
        
        result = content
        for citation in sorted_citations:
            # Find insertion point
            if citation.position < len(result):
                # Insert citation link
                citation_markdown = f" [{citation.anchor_text}]({citation.source_url})"
                result = result[:citation.position] + citation_markdown + result[citation.position:]
        
        return result
    
    def generate_references_section(
        self,
        sources: List[Dict[str, str]]
    ) -> str:
        """
        Generate a references section.
        
        Args:
            sources: List of source dictionaries
        
        Returns:
            Markdown-formatted references section
        """
        references = "\n\n## References\n\n"
        
        for i, source in enumerate(sources, 1):
            title = source.get('title', 'Untitled')
            url = source.get('url', '')
            references += f"{i}. [{title}]({url})\n"
        
        return references
    
    def _identify_citation_points(
        self,
        sentences: List[str],
        num_citations: int
    ) -> List[int]:
        """
        Identify natural points in content for citations.
        
        Args:
            sentences: List of sentences
            num_citations: Number of citations needed
        
        Returns:
            List of sentence indices for citations
        """
        if len(sentences) <= num_citations:
            return list(range(len(sentences)))
        
        # Distribute citations evenly throughout content
        step = len(sentences) // (num_citations + 1)
        points = [step * (i + 1) for i in range(num_citations)]
        
        return points[:num_citations]
    
    def _generate_anchor_text(self, title: str) -> str:
        """
        Generate anchor text from source title.
        
        Args:
            title: Source title
        
        Returns:
            Anchor text
        """
        # Use first few words of title
        words = title.split()[:5]
        return ' '.join(words)

