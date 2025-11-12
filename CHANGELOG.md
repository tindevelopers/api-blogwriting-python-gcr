## 1.2.0 (2025-01-10)

### Added
- **Enhanced Blog Generation Endpoint**: `POST /api/v1/blog/generate-enhanced`
  - 4-stage generation pipeline (Research → Draft → Enhancement → SEO Polish)
  - Intent-based content optimization using DataForSEO search intent analysis
  - Few-shot learning from top-ranking content examples
  - Content length optimization based on SERP competition analysis
  - Multi-model consensus generation (optional): Combines GPT-4o and Claude for higher quality
  - Google Knowledge Graph integration for entity recognition and structured data
  - Advanced semantic keyword integration using DataForSEO related keywords
  - Comprehensive 6-dimensional quality scoring (readability, SEO, structure, factual, uniqueness, engagement)
  - Content freshness signals: Current year/dates in prompts, "last updated" timestamps
  - Automatic citation generation and integration
  - SERP feature optimization (featured snippets, People Also Ask, etc.)
- **New Components**:
  - `IntentAnalyzer`: Analyzes search intent and optimizes content structure
  - `FewShotLearningExtractor`: Extracts examples from top-ranking content
  - `ContentLengthOptimizer`: Optimizes content length based on competition
  - `ConsensusGenerator`: Multi-model content synthesis
  - `GoogleKnowledgeGraphClient`: Entity extraction and structured data
  - `SemanticKeywordIntegrator`: Natural keyword integration
  - `ContentQualityScorer`: Multi-dimensional quality assessment
- **Enhanced Prompt Templates**: Current year/date included, freshness signals, intent-based recommendations
- **Documentation**: 
  - `ENHANCED_BLOG_GENERATION_GUIDE.md`: Complete API usage guide
  - `PHASE1_PHASE2_IMPLEMENTATION.md`: Phase 1 & 2 implementation details
  - `PHASE3_IMPLEMENTATION.md`: Phase 3 implementation details
  - `IMPLEMENTATION_COMPLETE.md`: Complete implementation summary

### Changed
- Enhanced prompt builder includes current year/date for freshness signals
- Pipeline now includes intent analysis, few-shot learning, and length optimization
- Quality scoring integrated into all enhanced blog generation
- Response includes `quality_score`, `quality_dimensions`, `structured_data`, `semantic_keywords`

### Performance
- Standard generation: ~10-15 seconds, $0.015-$0.030 per article
- With consensus: ~15-20 seconds, $0.040-$0.080 per article
- Quality scores typically 80-90/100 with all features enabled

### Notes
- All Phase 1, 2, and 3 recommendations from `BLOG_QUALITY_IMPROVEMENTS.md` now implemented
- Enhanced endpoint requires Google Custom Search API for full functionality
- DataForSEO integration recommended for intent analysis and semantic keywords
- Knowledge Graph API optional but recommended for structured data

---

## 1.1.0 (2025-11-10)

### Added
- New endpoint: `POST /api/v1/integrations/connect-and-recommend`
  - Target-agnostic integration input (`provider` label + opaque `connection` object).
  - Computes backlink and interlink recommendations from selected keywords.
  - Best-effort persistence to Supabase:
    - `integrations_{ENV}` for integration metadata.
    - `recommendations_{ENV}` for computed recommendations (aggregate + per-keyword).
- New Supabase schema file: `supabase_schema.sql` with environment-suffixed tables and optional RLS.
- WordPress import hardening: gracefully returns 501 if WP backend module isn’t installed.
- Enhanced keyword analysis endpoint: `POST /api/v1/keywords/enhanced` (uses DataForSEO when configured; graceful fallback).
- Phrase-mode for extraction: `/api/v1/keywords/extract` now supports `max_ngram` and `dedup_lim` to prefer multi-word keyphrases.
- DataForSEO client additions: keyword overview, related keywords, top searches, search intent helpers.

### Changed
- Documentation updated with version, publish date, new functionality highlights, and endpoint usage.
- DataForSEO credentials now prefer `DATAFORSEO_API_KEY` and `DATAFORSEO_API_SECRET` (fallback to legacy `DATAFORSEO_API_LOGIN`/`DATAFORSEO_API_PASSWORD`).

### Notes
- Develop environment deploys to `blog-writer-api-dev` in `europe-west1`.
- Service health: `/health` returns `{"status":"healthy"}` when deployment is live.


