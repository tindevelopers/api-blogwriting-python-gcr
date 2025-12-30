"""
Content Validation API

Provides endpoint for validating content quality before publishing.
Checks for artifacts, structure, SEO, links, and readability.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..utils.content_sanitizer import detect_artifacts, strip_markdown_for_analysis
from ..seo.readability_analyzer import ReadabilityAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/content", tags=["Content Validation"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ValidationChecks(BaseModel):
    """Which validation checks to perform."""
    artifacts: bool = Field(default=True, description="Check for LLM artifacts")
    structure: bool = Field(default=True, description="Check content structure (headings, etc.)")
    seo: bool = Field(default=True, description="Check SEO elements")
    links: bool = Field(default=True, description="Check internal/external links")
    readability: bool = Field(default=True, description="Check readability scores")


class ContentValidationRequest(BaseModel):
    """Request for content validation."""
    content: str = Field(..., min_length=100, description="HTML or markdown content to validate")
    title: Optional[str] = Field(None, description="Blog title")
    excerpt: Optional[str] = Field(None, description="Meta description/excerpt")
    keywords: List[str] = Field(default_factory=list, description="Target keywords")
    checks: ValidationChecks = Field(default_factory=ValidationChecks, description="Which checks to perform")


class ValidationIssue(BaseModel):
    """A single validation issue."""
    severity: str = Field(..., description="'error', 'warning', or 'info'")
    message: str = Field(..., description="Description of the issue")
    suggestion: Optional[str] = Field(None, description="How to fix the issue")


class CheckResult(BaseModel):
    """Result of a single validation check."""
    passed: bool = Field(..., description="Whether this check passed")
    issues: List[ValidationIssue] = Field(default_factory=list, description="Issues found")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Metrics for this check")


class ValidationSummary(BaseModel):
    """Summary of all validation issues."""
    errors: int = Field(default=0, description="Number of errors")
    warnings: int = Field(default=0, description="Number of warnings")
    info: int = Field(default=0, description="Number of info messages")


class ContentValidationResponse(BaseModel):
    """Response from content validation."""
    is_valid: bool = Field(..., description="Whether content passes all required checks")
    overall_score: int = Field(..., ge=0, le=100, description="Overall quality score 0-100")
    checks: Dict[str, CheckResult] = Field(..., description="Results of each check")
    summary: ValidationSummary = Field(..., description="Summary of issues by severity")


# ============================================================================
# Validation Endpoint
# ============================================================================

@router.post("/validate", response_model=ContentValidationResponse)
async def validate_content(request: ContentValidationRequest):
    """
    Validate content quality before publishing.
    
    Performs multiple quality checks based on the request:
    - **artifacts**: Checks for LLM preamble, meta-commentary, thinking tags
    - **structure**: Checks heading hierarchy, paragraph length, lists
    - **seo**: Checks keyword density, meta description, title length
    - **links**: Checks internal/external link count and quality
    - **readability**: Checks Flesch Reading Ease and sentence length
    
    Returns detailed results for each check with specific issues and suggestions.
    """
    try:
        content = request.content
        checks_to_perform = request.checks
        check_results: Dict[str, CheckResult] = {}
        
        # Run each requested check
        if checks_to_perform.artifacts:
            check_results["artifacts"] = _check_artifacts(content)
        
        if checks_to_perform.structure:
            check_results["structure"] = _check_structure(content)
        
        if checks_to_perform.seo:
            check_results["seo"] = _check_seo(
                content, 
                request.title, 
                request.excerpt, 
                request.keywords
            )
        
        if checks_to_perform.links:
            check_results["links"] = _check_links(content)
        
        if checks_to_perform.readability:
            check_results["readability"] = _check_readability(content)
        
        # Calculate summary
        summary = ValidationSummary()
        for check_result in check_results.values():
            for issue in check_result.issues:
                if issue.severity == "error":
                    summary.errors += 1
                elif issue.severity == "warning":
                    summary.warnings += 1
                else:
                    summary.info += 1
        
        # Determine overall validity (no errors = valid)
        is_valid = summary.errors == 0
        
        # Calculate overall score
        overall_score = _calculate_overall_score(check_results, summary)
        
        return ContentValidationResponse(
            is_valid=is_valid,
            overall_score=overall_score,
            checks=check_results,
            summary=summary
        )
        
    except Exception as e:
        logger.error(f"Content validation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


# ============================================================================
# Individual Check Functions
# ============================================================================

def _check_artifacts(content: str) -> CheckResult:
    """Check for LLM artifacts in content."""
    issues = []
    
    detected = detect_artifacts(content)
    
    for artifact in detected:
        issues.append(ValidationIssue(
            severity=artifact.get("severity", "warning"),
            message=artifact.get("description", "Artifact detected"),
            suggestion="Use the sanitization endpoint to clean content before publishing"
        ))
    
    passed = len([i for i in issues if i.severity == "error"]) == 0
    
    return CheckResult(
        passed=passed,
        issues=issues,
        metrics={
            "artifacts_detected": len(detected),
            "artifact_types": [a.get("type") for a in detected]
        }
    )


def _check_structure(content: str) -> CheckResult:
    """Check content structure."""
    issues = []
    
    # Count headings
    h1_matches = re.findall(r'^#\s+.+$', content, re.MULTILINE)
    h2_matches = re.findall(r'^##\s+.+$', content, re.MULTILINE)
    h3_matches = re.findall(r'^###\s+.+$', content, re.MULTILINE)
    
    h1_count = len(h1_matches)
    h2_count = len(h2_matches)
    h3_count = len(h3_matches)
    
    # Check for single H1
    if h1_count == 0:
        issues.append(ValidationIssue(
            severity="error",
            message="No H1 heading found",
            suggestion="Add exactly one H1 heading at the beginning of the content"
        ))
    elif h1_count > 1:
        issues.append(ValidationIssue(
            severity="warning",
            message=f"Multiple H1 headings found ({h1_count})",
            suggestion="Use only one H1 heading for the main title"
        ))
    
    # Check for minimum H2 sections
    if h2_count < 3:
        issues.append(ValidationIssue(
            severity="info",
            message=f"Only {h2_count} H2 headings found, recommend 3-5 for SEO",
            suggestion="Add more main sections to improve content depth"
        ))
    
    # Count paragraphs
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip() and not p.strip().startswith('#')]
    paragraph_count = len(paragraphs)
    
    # Count lists
    list_matches = re.findall(r'^[-*+]\s+.+$|^\d+\.\s+.+$', content, re.MULTILINE)
    list_count = len(list_matches)
    
    # Check for lists
    if h2_count > 0 and list_count < h2_count:
        issues.append(ValidationIssue(
            severity="info",
            message=f"Found {list_count} list items for {h2_count} sections",
            suggestion="Consider adding at least one list per section for scannability"
        ))
    
    passed = len([i for i in issues if i.severity == "error"]) == 0
    
    return CheckResult(
        passed=passed,
        issues=issues,
        metrics={
            "h1_count": h1_count,
            "h2_count": h2_count,
            "h3_count": h3_count,
            "paragraph_count": paragraph_count,
            "list_count": list_count
        }
    )


def _check_seo(
    content: str, 
    title: Optional[str], 
    excerpt: Optional[str], 
    keywords: List[str]
) -> CheckResult:
    """Check SEO elements."""
    issues = []
    
    primary_keyword = keywords[0] if keywords else None
    
    # Check title length
    if title:
        title_len = len(title)
        if title_len < 30:
            issues.append(ValidationIssue(
                severity="warning",
                message=f"Title is too short ({title_len} chars, recommend 50-60)",
                suggestion="Expand the title to be more descriptive"
            ))
        elif title_len > 70:
            issues.append(ValidationIssue(
                severity="warning",
                message=f"Title is too long ({title_len} chars, recommend 50-60)",
                suggestion="Shorten the title for better display in search results"
            ))
    
    # Check meta description length
    if excerpt:
        excerpt_len = len(excerpt)
        if excerpt_len < 120:
            issues.append(ValidationIssue(
                severity="warning",
                message=f"Meta description is too short ({excerpt_len} chars, recommend 150-160)",
                suggestion="Expand the meta description with more compelling copy"
            ))
        elif excerpt_len > 160:
            issues.append(ValidationIssue(
                severity="warning",
                message=f"Meta description is too long ({excerpt_len} chars, recommend 150-160)",
                suggestion="Shorten to prevent truncation in search results"
            ))
    
    # Check keyword in first paragraph
    if primary_keyword:
        # Get first 500 chars
        first_part = content[:500].lower()
        keyword_lower = primary_keyword.lower()
        
        if keyword_lower not in first_part:
            issues.append(ValidationIssue(
                severity="warning",
                message=f"Primary keyword '{primary_keyword}' not found in first paragraph",
                suggestion="Include primary keyword in introduction for better SEO"
            ))
        
        # Check keyword density
        content_lower = content.lower()
        word_count = len(content.split())
        keyword_count = content_lower.count(keyword_lower)
        
        if word_count > 0:
            density = (keyword_count / word_count) * 100
            if density < 0.5:
                issues.append(ValidationIssue(
                    severity="info",
                    message=f"Low keyword density ({density:.1f}%, recommend 1-2%)",
                    suggestion="Naturally incorporate the primary keyword more often"
                ))
            elif density > 3:
                issues.append(ValidationIssue(
                    severity="warning",
                    message=f"High keyword density ({density:.1f}%), may be flagged as keyword stuffing",
                    suggestion="Reduce keyword usage to feel more natural"
                ))
        else:
            density = 0
    else:
        density = 0
    
    passed = len([i for i in issues if i.severity == "error"]) == 0
    
    return CheckResult(
        passed=passed,
        issues=issues,
        metrics={
            "keyword_density": round(density, 2) if primary_keyword else None,
            "meta_description_length": len(excerpt) if excerpt else 0,
            "title_length": len(title) if title else 0
        }
    )


def _check_links(content: str) -> CheckResult:
    """Check internal and external links."""
    issues = []
    
    # Find all markdown links
    link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
    links = re.findall(link_pattern, content)
    
    internal_links = []
    external_links = []
    broken_links = []
    
    for anchor, url in links:
        # Skip image links
        if url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg')):
            continue
        
        if url.startswith('http://') or url.startswith('https://'):
            external_links.append({"anchor": anchor, "url": url})
        elif url.startswith('/') or url.startswith('#'):
            internal_links.append({"anchor": anchor, "url": url})
        else:
            # Relative path without leading slash - might be broken
            broken_links.append({"anchor": anchor, "url": url})
    
    internal_count = len(internal_links)
    external_count = len(external_links)
    
    # Check internal link count
    if internal_count < 3:
        issues.append(ValidationIssue(
            severity="error" if internal_count == 0 else "warning",
            message=f"Found {internal_count} internal link{'s' if internal_count != 1 else ''}, recommend 3-5",
            suggestion="Use 'Add Links' feature to insert more internal links"
        ))
    
    # Check for generic anchor text
    generic_anchors = ["click here", "read more", "learn more", "here", "link"]
    for link in internal_links + external_links:
        if link["anchor"].lower().strip() in generic_anchors:
            issues.append(ValidationIssue(
                severity="warning",
                message=f"Generic anchor text found: '{link['anchor']}'",
                suggestion="Use descriptive anchor text that indicates the destination content"
            ))
    
    passed = len([i for i in issues if i.severity == "error"]) == 0
    
    return CheckResult(
        passed=passed,
        issues=issues,
        metrics={
            "internal_links": internal_count,
            "external_links": external_count,
            "broken_links": len(broken_links)
        }
    )


def _check_readability(content: str) -> CheckResult:
    """Check readability metrics."""
    issues = []
    
    # Strip markdown for analysis
    plain_text = strip_markdown_for_analysis(content)
    
    # Use readability analyzer if available
    try:
        analyzer = ReadabilityAnalyzer()
        metrics = analyzer.analyze(plain_text)
        
        flesch_score = metrics.flesch_reading_ease
        avg_sentence_length = metrics.avg_sentence_length
        avg_paragraph_length = metrics.avg_paragraph_length
        
    except Exception as e:
        logger.warning(f"Readability analyzer failed: {e}")
        # Manual calculation fallback
        sentences = re.split(r'[.!?]+', plain_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        words = plain_text.split()
        
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * 1.5)  # Rough estimate
        avg_paragraph_length = len(sentences) / max(1, plain_text.count('\n\n') + 1)
    
    # Check Flesch score
    if flesch_score < 30:
        issues.append(ValidationIssue(
            severity="error",
            message=f"Very low readability score ({flesch_score:.0f}), content is too complex",
            suggestion="Simplify sentences and use shorter words"
        ))
    elif flesch_score < 50:
        issues.append(ValidationIssue(
            severity="warning",
            message=f"Low readability score ({flesch_score:.0f}), recommend 60-70",
            suggestion="Break up long sentences and simplify vocabulary"
        ))
    
    # Check sentence length
    if avg_sentence_length > 25:
        issues.append(ValidationIssue(
            severity="warning",
            message=f"Average sentence length is {avg_sentence_length:.0f} words, recommend 15-20",
            suggestion="Break long sentences into shorter ones"
        ))
    
    passed = len([i for i in issues if i.severity == "error"]) == 0
    
    return CheckResult(
        passed=passed,
        issues=issues,
        metrics={
            "flesch_score": round(flesch_score, 1),
            "avg_sentence_length": round(avg_sentence_length, 1),
            "avg_paragraph_length": round(avg_paragraph_length, 1) if 'avg_paragraph_length' in dir() else 0
        }
    )


def _calculate_overall_score(
    check_results: Dict[str, CheckResult], 
    summary: ValidationSummary
) -> int:
    """Calculate overall quality score 0-100."""
    # Base score
    score = 100
    
    # Deduct for issues
    score -= summary.errors * 15
    score -= summary.warnings * 5
    score -= summary.info * 1
    
    # Bonus for good metrics
    if "readability" in check_results:
        flesch = check_results["readability"].metrics.get("flesch_score", 50)
        if 60 <= flesch <= 70:
            score += 5  # Optimal readability bonus
    
    if "structure" in check_results:
        h2_count = check_results["structure"].metrics.get("h2_count", 0)
        if 3 <= h2_count <= 7:
            score += 3  # Good structure bonus
    
    if "links" in check_results:
        internal = check_results["links"].metrics.get("internal_links", 0)
        if 3 <= internal <= 5:
            score += 2  # Good linking bonus
    
    return max(0, min(100, score))

