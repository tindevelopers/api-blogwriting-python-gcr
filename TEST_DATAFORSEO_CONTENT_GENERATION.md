# DataForSEO Content Generation API - Direct Testing Guide

This guide explains how to test the DataForSEO Content Generation API directly.

## Overview

The test script `test_dataforseo_content_generation_direct.py` tests all three main DataForSEO Content Generation endpoints:

1. **Generate Text** - Generate content from a prompt
2. **Generate Subtopics** - Generate subtopics from text
3. **Generate Meta Tags** - Generate SEO meta titles and descriptions

## Prerequisites

1. **DataForSEO Account**: You need a DataForSEO account with Content Generation API access
2. **API Credentials**: Get your API credentials from DataForSEO dashboard:
   - API Key (username)
   - API Secret (password)

## Setup

### 1. Set Environment Variables

Export your DataForSEO credentials:

```bash
export DATAFORSEO_API_KEY="your_api_key_here"
export DATAFORSEO_API_SECRET="your_api_secret_here"
```

Or create a `.env` file (not committed to git):

```bash
DATAFORSEO_API_KEY=your_api_key_here
DATAFORSEO_API_SECRET=your_api_secret_here
```

Then load it:

```bash
source .env
```

### 2. Install Dependencies

Make sure you have the required Python packages:

```bash
pip install httpx
```

Or install all project dependencies:

```bash
pip install -r requirements.txt
```

## Running the Tests

### Run All Tests

```bash
python test_dataforseo_content_generation_direct.py
```

This will run:
- Test 1: Generate Text (short paragraph)
- Test 2: Generate Subtopics (5 subtopics)
- Test 3: Generate Meta Tags (title + description)
- Test 4: Complete Blog Generation Workflow (all three steps)

### Test Output

The script provides colored output:
- ✅ Green: Success
- ⚠️ Yellow: Warnings
- ❌ Red: Errors
- 🔵 Blue: Information

## Test Results

### Expected Output Structure

#### Generate Text
```json
{
  "success": true,
  "text": "Generated content here...",
  "tokens_used": 250,
  "metadata": {}
}
```

#### Generate Subtopics
```json
{
  "success": true,
  "subtopics": ["Topic 1", "Topic 2", "Topic 3"],
  "count": 3,
  "metadata": {}
}
```

#### Generate Meta Tags
```json
{
  "success": true,
  "meta_title": "SEO Optimized Title",
  "meta_description": "SEO optimized description...",
  "summary": "Content summary...",
  "keywords": ["keyword1", "keyword2"],
  "metadata": {}
}
```

## API Endpoints Tested

### 1. Generate Text
- **Endpoint**: `POST /v3/content_generation/generate_text/live`
- **Purpose**: Generate text content from a prompt
- **Parameters**:
  - `text`: Input prompt
  - `max_tokens`: Maximum tokens to generate
  - `temperature`: Creativity level (0.0-1.0)
- **Cost**: $0.00005 per new token

### 2. Generate Subtopics
- **Endpoint**: `POST /v3/content_generation/generate_subtopics/live`
- **Purpose**: Generate subtopics from input text
- **Parameters**:
  - `text`: Input text
  - `max_subtopics`: Maximum number of subtopics
  - `language`: Language code (e.g., "en")
- **Cost**: $0.0001 per task

### 3. Generate Meta Tags
- **Endpoint**: `POST /v3/content_generation/generate_meta_tags/live`
- **Purpose**: Generate SEO meta titles and descriptions
- **Parameters**:
  - `title`: Page title
  - `text`: Page content
  - `language`: Language code
- **Cost**: $0.001 per task

## Cost Estimation

For a typical blog post (~1,500 words ≈ 2,000 tokens):

- **Generate Text**: 2,000 tokens × $0.00005 = **$0.10**
- **Generate Subtopics**: 1 task × $0.0001 = **$0.0001**
- **Generate Meta Tags**: 1 task × $0.001 = **$0.001**
- **Total**: **~$0.10 per blog post**

## Troubleshooting

### Error: Credentials not found
```
❌ Error: DataForSEO credentials not found!
Please set DATAFORSEO_API_KEY and DATAFORSEO_API_SECRET environment variables.
```

**Solution**: Make sure you've exported the environment variables or loaded them from a `.env` file.

### Error: HTTP 401 Unauthorized
```
❌ HTTP Error: 401
```

**Solution**: Check that your API credentials are correct. Verify them in your DataForSEO dashboard.

### Error: HTTP 402 Payment Required
```
❌ HTTP Error: 402
```

**Solution**: Your DataForSEO account may not have sufficient credits or Content Generation API access. Check your account balance and subscription.

### Error: No result in response
```
⚠ No result in response
```

**Solution**: 
- Check the API response structure in the logs
- Verify your account has Content Generation API access
- Check if there are any API errors in the response

## Customizing Tests

You can modify the test script to test different scenarios:

### Test with Custom Prompt

```python
await tester.test_generate_text(
    prompt="Your custom prompt here",
    max_tokens=1000,
    temperature=0.8
)
```

### Test with Different Blog Topic

```python
await tester.test_complete_blog_generation(
    topic="Your Blog Topic",
    keywords=["keyword1", "keyword2", "keyword3"],
    word_count=1500
)
```

## Integration with Main Application

This test script uses the same API endpoints as the main application:

- `src/blog_writer_sdk/integrations/dataforseo_integration.py` - DataForSEO client
- `src/blog_writer_sdk/services/dataforseo_content_generation_service.py` - Content generation service

The test script validates that:
1. API credentials work correctly
2. API endpoints respond as expected
3. Response parsing is correct
4. Cost calculations are accurate

## Next Steps

After successful testing:

1. **Verify Integration**: Ensure the main application uses the same endpoints correctly
2. **Monitor Costs**: Track API usage and costs in production
3. **Optimize Prompts**: Refine prompts for better content quality
4. **Error Handling**: Implement proper error handling and fallbacks

## References

- [DataForSEO Content Generation API Docs](https://docs.dataforseo.com/v3/content_generation-overview/)
- [DataForSEO Pricing](https://dataforseo.com/pricing/content-generation-api/content-generation-api)
- [Project Documentation](./DATAFORSEO_CONTENT_GENERATION.md)

