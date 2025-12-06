"""
Citation and Source Integration

Automatically generates citations and integrates authoritative sources into content.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import logging
import os
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """Citation information."""
    text: str
    source_url: str
    source_title: str
    anchor_text: str
    position: int  # Character position in content
    domain_rank: Optional[int] = None  # Domain authority rank (0-1000)


@dataclass
class CitationResult:
    """Result of citation generation."""
    citations: List[Citation]
    sources_used: List[Dict[str, str]]
    citation_count: int
    warnings: List[str] = None  # API warnings and notices
    
    def __post_init__(self):
        """Initialize warnings list if None."""
        if self.warnings is None:
            self.warnings = []


class CitationGenerator:
    """Generates and integrates citations into content."""
    
    def __init__(self, google_search_client=None, dataforseo_client=None):
        """
        Initialize citation generator.
        
        Args:
            google_search_client: Google Custom Search client (optional)
            dataforseo_client: DataForSEO client for domain authority checking (optional)
        """
        self.google_search = google_search_client
        self.dataforseo_client = dataforseo_client
    
    async def generate_citations(
        self,
        content: str,
        topic: str,
        keywords: List[str],
        num_citations: int = 5,
        min_domain_rank: int = 20,
        prefer_high_rank: bool = True
    ) -> CitationResult:
        """
        Generate citations for content with domain authority checking.
        
        Args:
            content: Content to add citations to
            topic: Main topic
            keywords: Related keywords
            num_citations: Number of citations to generate
            min_domain_rank: Minimum domain rank to accept (0-1000, default: 20)
            prefer_high_rank: If True, prioritize domains with rank > 50
        
        Returns:
            CitationResult with citations and sources
        """
        citations = []
        sources_used = []
        api_warnings = []  # Collect API warnings
        
        if not self.google_search:
            warning_msg = "Google Custom Search API not available for citation generation"
            logger.warning(warning_msg)
            logger.warning(f"API_UNAVAILABLE: Google Custom Search API not configured. Citations cannot be generated.")
            return CitationResult(
                citations=[],
                sources_used=[],
                citation_count=0,
                warnings=[warning_msg]
            )
        
        # Find authoritative sources
        try:
            # Get more sources than needed to allow filtering by domain rank
            search_results = num_citations * 2 if self.dataforseo_client else num_citations
            sources = await self.google_search.search_for_sources(
                topic, keywords, num_results=search_results
            )
            
            # Check domain ranks if DataForSEO client is available
            filtered_sources = sources
            if self.dataforseo_client and sources:
                try:
                    # Extract domains from URLs
                    domains = []
                    domain_to_sources = {}
                    for source in sources:
                        url = source.get('link', '')
                        if url:
                            parsed = urlparse(url)
                            domain = parsed.netloc.replace('www.', '')
                            if domain:
                                domains.append(domain)
                                if domain not in domain_to_sources:
                                    domain_to_sources[domain] = []
                                domain_to_sources[domain].append(source)
                    
                    if domains:
                        # Get domain ranks
                        tenant_id = os.getenv("TENANT_ID", "default")
                        domain_ranks = await self.dataforseo_client.get_domain_ranks(
                            domains=domains,
                            tenant_id=tenant_id
                        )
                        
                        # Filter and rank sources by domain authority
                        ranked_sources = []
                        for source in sources:
                            url = source.get('link', '')
                            if url:
                                parsed = urlparse(url)
                                domain = parsed.netloc.replace('www.', '')
                                rank = domain_ranks.get(domain, 0)
                                
                                # Filter out low-authority domains
                                if rank >= min_domain_rank:
                                    source['domain_rank'] = rank
                                    ranked_sources.append(source)
                        
                        # Sort by domain rank (highest first) if prefer_high_rank
                        if prefer_high_rank:
                            ranked_sources.sort(key=lambda x: x.get('domain_rank', 0), reverse=True)
                            # Prioritize domains with rank > 50
                            high_rank_sources = [s for s in ranked_sources if s.get('domain_rank', 0) > 50]
                            low_rank_sources = [s for s in ranked_sources if s.get('domain_rank', 0) <= 50]
                            filtered_sources = high_rank_sources + low_rank_sources
                        else:
                            filtered_sources = ranked_sources
                        
                        logger.info(f"Filtered {len(sources)} sources to {len(filtered_sources)} based on domain rank (min: {min_domain_rank})")
                except Exception as e:
                    error_msg = f"DataForSEO Backlinks API unavailable: {str(e)}"
                    logger.error(f"Domain rank checking failed: {error_msg}", exc_info=True)
                    logger.warning(f"API_UNAVAILABLE: DataForSEO Backlinks API (bulk_ranks) failed. Error: {type(e).__name__}: {str(e)}")
                    api_warnings.append(f"Citation quality optimization unavailable: Domain authority checking failed. Using all sources without domain rank filtering.")
                    filtered_sources = sources
            
            # Take top sources after filtering
            filtered_sources = filtered_sources[:num_citations]
            
            # Generate citations at natural points in content
            sentences = content.split('.')
            citation_points = self._identify_citation_points(sentences, len(filtered_sources))
            
            for i, (sentence_idx, source) in enumerate(zip(citation_points, filtered_sources)):
                domain_rank = source.get('domain_rank')
                citation = Citation(
                    text=sentences[sentence_idx] if sentence_idx < len(sentences) else "",
                    source_url=source.get('link', ''),
                    source_title=source.get('title', ''),
                    anchor_text=self._generate_anchor_text(source.get('title', '')),
                    position=len('. '.join(sentences[:sentence_idx])) if sentence_idx > 0 else 0,
                    domain_rank=domain_rank
                )
                citations.append(citation)
                sources_used.append({
                    'url': source.get('link', ''),
                    'title': source.get('title', ''),
                    'snippet': source.get('snippet', ''),
                    'domain_rank': domain_rank
                })
        except Exception as e:
            error_msg = f"Citation generation failed: {str(e)}"
            logger.error(f"Citation generation failed: {error_msg}", exc_info=True)
            logger.error(f"API_ERROR: Citation generation exception. Error: {type(e).__name__}: {str(e)}")
            api_warnings.append(f"Citation generation encountered an error: {error_msg}")
        
        return CitationResult(
            citations=citations,
            sources_used=sources_used,
            citation_count=len(citations),
            warnings=api_warnings
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

