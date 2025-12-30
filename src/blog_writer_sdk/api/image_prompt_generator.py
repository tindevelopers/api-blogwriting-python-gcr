"""
Image Prompt Generation for Blog Content

Content-aware image prompt generation from blog sections.
Supports:
- Content-aware prompt generation
- Multiple prompt variations
- Style matching to content tone
- Placement suggestions
"""

import re
import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ImageType(str, Enum):
    """Types of images for blog content."""
    FEATURED = "featured"
    SECTION_HEADER = "section_header"
    INFOGRAPHIC = "infographic"
    ILLUSTRATION = "illustration"
    PRODUCT = "product"
    DIAGRAM = "diagram"


class ImageStyle(str, Enum):
    """Image styles matching content tone."""
    PHOTOGRAPHIC = "photographic"
    DIGITAL_ART = "digital_art"
    MINIMALIST = "minimalist"
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    TECHNICAL = "technical"


@dataclass
class ImagePrompt:
    """Generated image prompt with metadata."""
    prompt: str
    image_type: ImageType
    style: ImageStyle
    aspect_ratio: str
    placement_suggestion: Dict[str, Any]
    variations: List[str]
    alt_text_suggestion: str


@dataclass
class ImagePlacementSuggestion:
    """Suggestion for image placement in content."""
    image_type: ImageType
    position: int  # Character position in content
    section_title: Optional[str]
    prompt: str
    style: ImageStyle
    aspect_ratio: str
    priority: int  # 1-5, higher is more important


class ImagePromptGenerator:
    """Generate content-aware image prompts from blog content."""
    
    def __init__(self):
        """Initialize image prompt generator."""
        pass
    
    def analyze_content_for_images(
        self,
        content: str,
        topic: str,
        keywords: List[str],
        tone: str = "professional"
    ) -> List[ImagePlacementSuggestion]:
        """
        Analyze blog content and suggest image placements.
        
        Args:
            content: Blog content in markdown format
            topic: Main topic
            keywords: Related keywords
            tone: Content tone (professional, casual, etc.)
        
        Returns:
            List of image placement suggestions
        """
        suggestions = []
        
        # Extract sections from content
        sections = self._extract_sections(content)
        
        # Suggest featured image (always first)
        featured_suggestion = self._generate_featured_image_suggestion(
            topic, keywords, tone
        )
        suggestions.append(featured_suggestion)
        
        # Suggest section images (every 300-500 words)
        word_count = len(content.split())
        target_section_images = max(1, int(word_count / 400))  # ~1 per 400 words
        
        for i, section in enumerate(sections[:target_section_images]):
            if i == 0:  # Skip intro section (already has featured)
                continue
            
            section_suggestion = self._generate_section_image_suggestion(
                section, topic, keywords, tone, i
            )
            if section_suggestion:
                suggestions.append(section_suggestion)
        
        # Suggest infographic for long content (>2000 words)
        if word_count > 2000:
            infographic_suggestion = self._generate_infographic_suggestion(
                topic, keywords, sections
            )
            suggestions.append(infographic_suggestion)
        
        return suggestions
    
    def generate_prompt_from_section(
        self,
        section_content: str,
        section_title: Optional[str],
        topic: str,
        keywords: List[str],
        image_type: ImageType = ImageType.SECTION_HEADER,
        tone: str = "professional"
    ) -> ImagePrompt:
        """
        Generate image prompt from a blog section.
        
        Args:
            section_content: Content of the section
            section_title: Title of the section (if any)
            topic: Main topic
            keywords: Related keywords
            image_type: Type of image to generate
            tone: Content tone
        
        Returns:
            ImagePrompt with prompt and metadata
        """
        # Extract key concepts from section
        key_concepts = self._extract_key_concepts(section_content, keywords)
        
        # Generate base prompt
        base_prompt = self._build_base_prompt(
            key_concepts, section_title, topic, image_type, tone
        )
        
        # Generate variations
        variations = self._generate_prompt_variations(
            base_prompt, key_concepts, image_type
        )
        
        # Determine style based on tone
        style = self._determine_style_from_tone(tone, image_type)
        
        # Determine aspect ratio
        aspect_ratio = self._determine_aspect_ratio(image_type)
        
        # Generate alt text suggestion
        alt_text = self._generate_alt_text(
            key_concepts, section_title, topic, image_type
        )
        
        return ImagePrompt(
            prompt=base_prompt,
            image_type=image_type,
            style=style,
            aspect_ratio=aspect_ratio,
            placement_suggestion={
                "section": section_title or "Introduction",
                "position": "before_section"
            },
            variations=variations,
            alt_text_suggestion=alt_text
        )
    
    def generate_featured_image_prompt(
        self,
        topic: str,
        keywords: List[str],
        tone: str = "professional"
    ) -> ImagePrompt:
        """
        Generate prompt for featured image.
        
        Args:
            topic: Main topic
            keywords: Related keywords
            tone: Content tone
        
        Returns:
            ImagePrompt for featured image
        """
        primary_keyword = keywords[0] if keywords else topic
        
        prompt = f"Professional blog post featured image: {topic}. "
        prompt += f"Main concept: {primary_keyword}. "
        prompt += f"Style: {tone}, high quality, visually appealing, suitable for blog header"
        
        variations = [
            f"Featured image for blog post about {topic}",
            f"Professional header image: {primary_keyword}",
            f"Blog post featured image showcasing {topic}",
            f"High-quality blog header: {topic} concept"
        ]
        
        style = self._determine_style_from_tone(tone, ImageType.FEATURED)
        
        return ImagePrompt(
            prompt=prompt,
            image_type=ImageType.FEATURED,
            style=style,
            aspect_ratio="16:9",
            placement_suggestion={
                "section": "Introduction",
                "position": "after_h1"
            },
            variations=variations,
            alt_text_suggestion=f"Featured image for {topic}"
        )
    
    def _extract_sections(self, content: str) -> List[Dict[str, Any]]:
        """Extract sections from markdown content."""
        sections = []
        
        # Split by H2 headings
        h2_pattern = r'^##\s+(.+)$'
        matches = list(re.finditer(h2_pattern, content, re.MULTILINE))
        
        for i, match in enumerate(matches):
            section_title = match.group(1).strip()
            start_pos = match.start()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            
            section_content = content[start_pos:end_pos]
            
            sections.append({
                "title": section_title,
                "content": section_content,
                "position": start_pos,
                "word_count": len(section_content.split())
            })
        
        return sections
    
    def _extract_key_concepts(
        self,
        content: str,
        keywords: List[str]
    ) -> List[str]:
        """Extract key concepts from content."""
        concepts = []
        
        # Extract nouns and important phrases
        # Simple approach: look for capitalized words and keyword-related terms
        words = content.split()
        
        # Add keywords
        concepts.extend(keywords[:3])
        
        # Extract capitalized phrases (potential concepts)
        capitalized_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        capitalized = re.findall(capitalized_pattern, content)
        concepts.extend([c for c in capitalized if len(c) > 3][:5])
        
        # Remove duplicates and limit
        concepts = list(dict.fromkeys(concepts))[:8]
        
        return concepts
    
    def _build_base_prompt(
        self,
        key_concepts: List[str],
        section_title: Optional[str],
        topic: str,
        image_type: ImageType,
        tone: str
    ) -> str:
        """Build base image prompt."""
        concepts_str = ", ".join(key_concepts[:5])
        
        if image_type == ImageType.FEATURED:
            return f"Professional blog post featured image: {topic}. Main concepts: {concepts_str}. Style: {tone}, high quality"
        elif image_type == ImageType.SECTION_HEADER:
            section_part = f" for section '{section_title}'" if section_title else ""
            return f"Blog section header image{section_part}: {topic}. Concepts: {concepts_str}. Style: {tone}"
        elif image_type == ImageType.INFOGRAPHIC:
            return f"Infographic illustration: {topic}. Key concepts: {concepts_str}. Style: {tone}, informative, visual"
        else:
            return f"Blog illustration: {topic}. Concepts: {concepts_str}. Style: {tone}"
    
    def _generate_prompt_variations(
        self,
        base_prompt: str,
        key_concepts: List[str],
        image_type: ImageType
    ) -> List[str]:
        """Generate variations of the prompt."""
        variations = []
        
        # Variation 1: More detailed
        variations.append(base_prompt + ", detailed, high resolution")
        
        # Variation 2: Simpler
        if key_concepts:
            variations.append(f"Simple illustration: {key_concepts[0]}")
        
        # Variation 3: Different angle
        variations.append(base_prompt + ", alternative perspective")
        
        # Variation 4: Stylized
        variations.append(base_prompt + ", stylized, artistic")
        
        return variations[:4]
    
    def _determine_style_from_tone(
        self,
        tone: str,
        image_type: ImageType
    ) -> ImageStyle:
        """Determine image style from content tone."""
        tone_lower = tone.lower()
        
        if "professional" in tone_lower or "formal" in tone_lower:
            return ImageStyle.PHOTOGRAPHIC if image_type == ImageType.FEATURED else ImageStyle.PROFESSIONAL
        elif "casual" in tone_lower or "friendly" in tone_lower:
            return ImageStyle.CASUAL
        elif "technical" in tone_lower:
            return ImageStyle.TECHNICAL
        else:
            return ImageStyle.PHOTOGRAPHIC
    
    def _determine_aspect_ratio(self, image_type: ImageType) -> str:
        """Determine aspect ratio based on image type."""
        ratios = {
            ImageType.FEATURED: "16:9",
            ImageType.SECTION_HEADER: "4:3",
            ImageType.INFOGRAPHIC: "16:9",
            ImageType.ILLUSTRATION: "4:3",
            ImageType.PRODUCT: "1:1",
            ImageType.DIAGRAM: "16:9"
        }
        return ratios.get(image_type, "16:9")
    
    def _generate_alt_text(
        self,
        key_concepts: List[str],
        section_title: Optional[str],
        topic: str,
        image_type: ImageType
    ) -> str:
        """Generate alt text suggestion."""
        if image_type == ImageType.FEATURED:
            return f"Featured image for {topic}"
        elif section_title:
            return f"Image for section: {section_title} about {topic}"
        else:
            concepts = ", ".join(key_concepts[:3])
            return f"Image illustrating {concepts} related to {topic}"
    
    def _generate_featured_image_suggestion(
        self,
        topic: str,
        keywords: List[str],
        tone: str
    ) -> ImagePlacementSuggestion:
        """Generate featured image suggestion."""
        prompt_gen = self.generate_featured_image_prompt(topic, keywords, tone)
        
        return ImagePlacementSuggestion(
            image_type=ImageType.FEATURED,
            position=0,
            section_title="Introduction",
            prompt=prompt_gen.prompt,
            style=prompt_gen.style,
            aspect_ratio=prompt_gen.aspect_ratio,
            priority=5  # Highest priority
        )
    
    def _generate_section_image_suggestion(
        self,
        section: Dict[str, Any],
        topic: str,
        keywords: List[str],
        tone: str,
        index: int
    ) -> Optional[ImagePlacementSuggestion]:
        """Generate section image suggestion."""
        if section["word_count"] < 200:  # Skip short sections
            return None
        
        prompt_gen = self.generate_prompt_from_section(
            section["content"],
            section["title"],
            topic,
            keywords,
            ImageType.SECTION_HEADER,
            tone
        )
        
        return ImagePlacementSuggestion(
            image_type=ImageType.SECTION_HEADER,
            position=section["position"],
            section_title=section["title"],
            prompt=prompt_gen.prompt,
            style=prompt_gen.style,
            aspect_ratio=prompt_gen.aspect_ratio,
            priority=3  # Medium priority
        )
    
    def _generate_infographic_suggestion(
        self,
        topic: str,
        keywords: List[str],
        sections: List[Dict[str, Any]]
    ) -> ImagePlacementSuggestion:
        """Generate infographic suggestion."""
        key_concepts = keywords[:5]
        concepts_str = ", ".join(key_concepts)
        
        prompt = f"Infographic illustration: {topic}. Key concepts: {concepts_str}. Informative, visual, data-driven"
        
        return ImagePlacementSuggestion(
            image_type=ImageType.INFOGRAPHIC,
            position=len(sections) // 2,  # Middle of content
            section_title="Main Content",
            prompt=prompt,
            style=ImageStyle.PROFESSIONAL,
            aspect_ratio="16:9",
            priority=4  # High priority
        )

