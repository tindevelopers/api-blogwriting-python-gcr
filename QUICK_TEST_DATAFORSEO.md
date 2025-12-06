# Quick Test Guide - DataForSEO Content Generation API

## Quick Start

1. **Set credentials**:
   ```bash
   export DATAFORSEO_API_KEY="your_key"
   export DATAFORSEO_API_SECRET="your_secret"
   ```

2. **Run test**:
   ```bash
   python3 test_dataforseo_content_generation_direct.py
   ```

## What It Tests

✅ **Generate Text** - Creates content from prompts  
✅ **Generate Subtopics** - Extracts subtopics from text  
✅ **Generate Meta Tags** - Generates SEO titles/descriptions  
✅ **Complete Workflow** - Full blog generation pipeline  

## Expected Output

The script will:
- Test each endpoint individually
- Show colored output (green = success, red = errors)
- Display generated content, subtopics, and meta tags
- Calculate API costs
- Provide detailed error messages if something fails

## Files Created

- `test_dataforseo_content_generation_direct.py` - Main test script
- `TEST_DATAFORSEO_CONTENT_GENERATION.md` - Detailed documentation
- `QUICK_TEST_DATAFORSEO.md` - This quick reference

## Troubleshooting

**No credentials?** → Set `DATAFORSEO_API_KEY` and `DATAFORSEO_API_SECRET`  
**401 Error?** → Check credentials are correct  
**402 Error?** → Check account balance/subscription  
**No results?** → Verify Content Generation API access in your account  

For detailed information, see `TEST_DATAFORSEO_CONTENT_GENERATION.md`

