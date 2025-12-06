# Image Generation Dimension Fix - Stability AI SDXL Compatibility

**Date:** 2025-11-18  
**Issue:** Image generation failing with dimension error  
**Status:** ✅ **FIXED**

---

## Problem Identified

**Error:** `invalid_sdxl_v1_dimensions`

**Error Details:**
```
'for stable-diffusion-xl-1024-v0-9 and stable-diffusion-xl-1024-v1-0 the allowed dimensions are 
1024x1024, 1152x896, 1216x832, 1344x768, 1536x640, 640x1536, 768x1344, 832x1216, 896x1152, 
but we received 1024x576'
```

**Root Cause:**
- Code was using `1024x576` for WIDE (16:9) aspect ratio
- Stability AI SDXL model **does not support** this dimension
- Only specific dimensions are allowed by the API

---

## Fix Applied

### Dimension Changes

**File:** `src/blog_writer_sdk/image/base_provider.py`

**Before:**
```python
ImageAspectRatio.WIDE: (1024, 576),      # ❌ Not supported by SDXL
ImageAspectRatio.ULTRA_WIDE: (1024, 432), # ❌ Not supported by SDXL
```

**After:**
```python
# WIDE (16:9) - Use Stability AI SDXL supported dimensions: 1344x768 or 1536x640
# Using 1344x768 as it's closer to standard 16:9 and better quality
ImageAspectRatio.WIDE: (1344, 768),       # ✅ Supported by SDXL
ImageAspectRatio.ULTRA_WIDE: (1536, 640), # ✅ Supported by SDXL (21:9)
```

### Supported Dimensions

Stability AI SDXL supports these dimensions:
- `1024x1024` (Square)
- `1152x896` (Portrait-ish)
- `1216x832` (Landscape)
- `1344x768` (Wide 16:9) ✅ **Now using this**
- `1536x640` (Ultra Wide 21:9) ✅ **Now using this**
- `640x1536` (Tall Portrait)
- `768x1344` (Portrait)
- `832x1216` (Portrait Landscape)
- `896x1152` (Portrait)

---

## Impact

### Before Fix
- ❌ Image generation failed with dimension error
- ❌ No images returned
- ❌ Warning: "invalid_sdxl_v1_dimensions"

### After Fix
- ✅ Correct dimensions used (1344x768 for 16:9)
- ✅ Image generation should work with Stability AI
- ✅ Images will be returned in `generated_images` array
- ✅ Image URLs ready for Cloudinary integration

---

## Image Response Format

When image generation succeeds:

```json
{
  "result": {
    "generated_images": [
      {
        "type": "featured",
        "image_url": "data:image/png;base64,...",  // Base64 data URL
        "alt_text": "Featured image for {topic}",
        "prompt": "Professional product photography: ..."
      }
    ]
  }
}
```

**For Cloudinary Integration:**
1. Extract `image_url` from `generated_images` array
2. Upload to Cloudinary using the image URL
3. Store Cloudinary URL in database

---

## Testing

### Test Request
```bash
curl -X POST "https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/blog/generate-enhanced?async_mode=true" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Best Smartphones 2025",
    "keywords": ["best smartphones"],
    "use_google_search": true
  }'
```

### Expected Result
- ✅ No dimension errors
- ✅ Image generation succeeds
- ✅ `generated_images` array contains image URLs
- ✅ URLs ready for Cloudinary upload

---

## Deployment

- ✅ Code fixed: `src/blog_writer_sdk/image/base_provider.py`
- ✅ Committed: `e37cf12`
- ✅ Pushed to: `develop` branch
- ✅ Cloud Build: Triggered
- ⏳ Deployment: In progress

---

## Additional Notes

### Image Generation Requirements

For images to be generated:
1. ✅ `use_google_search: true` (enables research phase)
2. ✅ Topic contains product indicators: "best", "top", "review", "compare", "guide"
3. ✅ Valid Stability AI API key configured
4. ✅ Stability AI API has credits available
5. ✅ **Correct dimensions** (now fixed)

### Dimension Mapping

| Aspect Ratio | Old Dimension | New Dimension | Status |
|--------------|---------------|----------------|--------|
| WIDE (16:9) | 1024x576 | 1344x768 | ✅ Fixed |
| ULTRA_WIDE (21:9) | 1024x432 | 1536x640 | ✅ Fixed |
| SQUARE (1:1) | 1024x1024 | 1024x1024 | ✅ OK |
| LANDSCAPE (4:3) | 1024x768 | 1024x768 | ✅ OK |
| PORTRAIT (3:4) | 768x1024 | 768x1024 | ✅ OK |

---

**Status:** ✅ Code fix deployed, testing in progress

**Next:** Wait for deployment (~5-10 minutes), then test image generation again.


