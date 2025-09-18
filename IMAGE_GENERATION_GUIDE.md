# Image Generation API Guide

## Overview

The Blog Writer SDK API includes a comprehensive Image Generation system that allows frontend applications to generate, edit, and enhance images using various AI providers. The system currently supports Stability AI with an extensible architecture for adding more providers in the future.

## Supported Image Providers

### 1. Stability AI
- **Provider Type**: `stability_ai`
- **Models**: Stable Diffusion XL, Stable Diffusion 3.5, and other SD models
- **Features**: Text-to-image, image variations, upscaling, inpainting, outpainting
- **Pricing**: Per-image pricing model
- **Max Resolution**: 2048x2048

## Image Generation Features

### 1. Text-to-Image Generation
Generate images from text prompts with customizable styles, aspect ratios, and quality settings.

### 2. Image Variations
Create multiple variations of an existing image with adjustable variation strength.

### 3. Image Upscaling
Enhance image resolution while preserving quality and details.

### 4. Image Editing
Edit images using inpainting (modify specific areas) or outpainting (extend beyond boundaries).

### 5. Asynchronous Processing
Background job processing for batch operations and long-running tasks.

## API Endpoints

### Base URL
All image generation endpoints are prefixed with `/api/v1/images`

### 1. Generate Image
**POST** `/api/v1/images/generate`

Generate an image from a text prompt.

**Request Body:**
```json
{
  "prompt": "A beautiful sunset over a mountain landscape",
  "provider": "stability_ai",
  "style": "photographic",
  "aspect_ratio": "16:9",
  "quality": "high",
  "negative_prompt": "blurry, low quality",
  "seed": 12345,
  "steps": 30,
  "guidance_scale": 7.0,
  "width": 1920,
  "height": 1080,
  "tags": ["landscape", "sunset", "nature"]
}
```

**Response:**
```json
{
  "success": true,
  "images": [
    {
      "image_id": "uuid-here",
      "image_url": "https://example.com/image.png",
      "image_data": "base64-encoded-image-data",
      "width": 1920,
      "height": 1080,
      "format": "png",
      "size_bytes": 2048576,
      "seed": 12345,
      "steps": 30,
      "guidance_scale": 7.0,
      "created_at": "2024-01-15T10:30:00Z",
      "provider": "stability_ai",
      "model": "stable-diffusion-xl-1024-v1-0",
      "quality_score": 0.95,
      "safety_score": 0.98
    }
  ],
  "generation_time_seconds": 12.5,
  "provider": "stability_ai",
  "model": "stable-diffusion-xl-1024-v1-0",
  "cost": 0.008,
  "request_id": "req-12345",
  "prompt_used": "A beautiful sunset over a mountain landscape"
}
```

### 2. Generate Image Variations
**POST** `/api/v1/images/variations`

Generate variations of an existing image.

**Request Body:**
```json
{
  "source_image_url": "https://example.com/source-image.jpg",
  "provider": "stability_ai",
  "variation_strength": 0.7,
  "num_variations": 4,
  "style": "digital_art",
  "seed": 54321
}
```

### 3. Upscale Image
**POST** `/api/v1/images/upscale`

Upscale an existing image to higher resolution.

**Request Body:**
```json
{
  "source_image_url": "https://example.com/image-to-upscale.jpg",
  "provider": "stability_ai",
  "scale_factor": 2.0,
  "quality": "high",
  "preserve_details": true,
  "enhance_colors": false
}
```

### 4. Edit Image
**POST** `/api/v1/images/edit`

Edit an existing image using inpainting or outpainting.

**Request Body:**
```json
{
  "source_image_url": "https://example.com/source-image.jpg",
  "mask_image_url": "https://example.com/mask-image.png",
  "prompt": "Add a beautiful garden in the background",
  "provider": "stability_ai",
  "edit_type": "inpaint",
  "strength": 0.8,
  "seed": 98765,
  "guidance_scale": 7.5
}
```

### 5. Create Image Generation Job
**POST** `/api/v1/images/jobs`

Create an asynchronous image generation job.

**Request Body:**
```json
{
  "prompt": "A futuristic cityscape at night",
  "provider": "stability_ai",
  "style": "sci_fi",
  "aspect_ratio": "21:9",
  "quality": "ultra"
}
```

**Response:**
```json
{
  "job_id": "job-uuid-here",
  "status": "queued"
}
```

### 6. Get Job Status
**GET** `/api/v1/images/jobs/{job_id}`

Get the status and result of an image generation job.

**Response:**
```json
{
  "job_id": "job-uuid-here",
  "status": "completed",
  "request": {
    "prompt": "A futuristic cityscape at night",
    "provider": "stability_ai"
  },
  "progress_percentage": 100.0,
  "result": {
    "success": true,
    "images": [...],
    "generation_time_seconds": 15.2
  },
  "created_at": "2024-01-15T10:30:00Z",
  "started_at": "2024-01-15T10:30:05Z",
  "completed_at": "2024-01-15T10:30:20Z"
}
```

### 7. List Jobs
**GET** `/api/v1/images/jobs`

List image generation jobs with optional filtering.

**Query Parameters:**
- `status`: Filter by job status (queued, processing, completed, failed, cancelled)
- `limit`: Number of jobs to return (default: 50)
- `offset`: Number of jobs to skip (default: 0)

### 8. Cancel Job
**DELETE** `/api/v1/images/jobs/{job_id}`

Cancel a pending or running image generation job.

### 9. List Providers
**GET** `/api/v1/images/providers`

List all configured image generation providers.

**Response:**
```json
{
  "stability_ai_1642248600": {
    "provider_type": "stability_ai",
    "status": "configured",
    "enabled": true,
    "priority": 1,
    "supported_styles": ["photographic", "digital_art", "painting"],
    "supported_aspect_ratios": ["1:1", "16:9", "4:3"],
    "max_resolution": "2048x2048"
  }
}
```

### 10. Configure Provider
**POST** `/api/v1/images/providers/configure`

Configure an image generation provider.

**Request Body:**
```json
{
  "provider_type": "stability_ai",
  "api_key": "sk-...",
  "enabled": true,
  "priority": 1,
  "default_model": "stable-diffusion-xl-1024-v1-0"
}
```

### 11. Health Check Providers
**GET** `/api/v1/images/providers/health`

Perform health checks on all image generation providers.

### 12. Remove Provider
**DELETE** `/api/v1/images/providers/{provider_name}`

Remove a configured image generation provider.

## Image Styles

The system supports various image styles:

- `photographic` - Realistic photographs
- `digital_art` - Digital artwork
- `painting` - Traditional painting style
- `sketch` - Hand-drawn sketches
- `cartoon` - Cartoon/animated style
- `anime` - Anime/manga style
- `realistic` - Hyper-realistic images
- `abstract` - Abstract art
- `minimalist` - Minimalist design
- `vintage` - Vintage/retro style
- `cyberpunk` - Cyberpunk aesthetic
- `fantasy` - Fantasy art
- `sci_fi` - Science fiction
- `watercolor` - Watercolor painting
- `oil_painting` - Oil painting style

## Aspect Ratios

Supported aspect ratios:

- `1:1` - Square (1024x1024)
- `3:4` - Portrait (768x1024)
- `4:3` - Landscape (1024x768)
- `16:9` - Wide (1024x576)
- `21:9` - Ultra-wide (1024x432)
- `2:3` - Tall (768x1152)
- `custom` - Custom dimensions

## Quality Levels

- `draft` - Fast generation, lower quality
- `standard` - Balanced quality and speed
- `high` - High quality generation
- `ultra` - Maximum quality, slower generation

## Frontend Integration Examples

### React/Next.js Example

```typescript
import { useState } from 'react';

interface ImageGenerationRequest {
  prompt: string;
  style?: string;
  aspect_ratio?: string;
  quality?: string;
}

export const useImageGeneration = () => {
  const [generating, setGenerating] = useState(false);
  const [images, setImages] = useState([]);

  const generateImage = async (request: ImageGenerationRequest) => {
    setGenerating(true);
    try {
      const response = await fetch('/api/v1/images/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: 'stability_ai',
          ...request
        })
      });
      
      const result = await response.json();
      setImages(result.images);
      return result;
    } catch (error) {
      console.error('Image generation failed:', error);
      throw error;
    } finally {
      setGenerating(false);
    }
  };

  const generateVariations = async (imageUrl: string, strength: number = 0.7) => {
    try {
      const response = await fetch('/api/v1/images/variations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_image_url: imageUrl,
          provider: 'stability_ai',
          variation_strength: strength,
          num_variations: 4
        })
      });
      
      return await response.json();
    } catch (error) {
      console.error('Image variation failed:', error);
      throw error;
    }
  };

  const upscaleImage = async (imageUrl: string, scale: number = 2.0) => {
    try {
      const response = await fetch('/api/v1/images/upscale', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_image_url: imageUrl,
          provider: 'stability_ai',
          scale_factor: scale,
          quality: 'high'
        })
      });
      
      return await response.json();
    } catch (error) {
      console.error('Image upscaling failed:', error);
      throw error;
    }
  };

  return {
    generating,
    images,
    generateImage,
    generateVariations,
    upscaleImage
  };
};
```

### Vue.js Example

```vue
<template>
  <div class="image-generation">
    <h2>Image Generation</h2>
    
    <!-- Generation Form -->
    <form @submit.prevent="generateImage">
      <textarea 
        v-model="prompt" 
        placeholder="Describe the image you want to generate..."
        required
      ></textarea>
      
      <select v-model="style">
        <option value="">Select Style (Optional)</option>
        <option value="photographic">Photographic</option>
        <option value="digital_art">Digital Art</option>
        <option value="painting">Painting</option>
        <option value="anime">Anime</option>
        <option value="fantasy">Fantasy</option>
      </select>
      
      <select v-model="aspectRatio">
        <option value="1:1">Square (1:1)</option>
        <option value="16:9">Wide (16:9)</option>
        <option value="4:3">Landscape (4:3)</option>
        <option value="3:4">Portrait (3:4)</option>
      </select>
      
      <select v-model="quality">
        <option value="standard">Standard</option>
        <option value="high">High</option>
        <option value="ultra">Ultra</option>
      </select>
      
      <button type="submit" :disabled="generating">
        {{ generating ? 'Generating...' : 'Generate Image' }}
      </button>
    </form>

    <!-- Generated Images -->
    <div v-if="images.length > 0" class="images-grid">
      <div 
        v-for="image in images" 
        :key="image.image_id"
        class="image-card"
      >
        <img :src="image.image_url" :alt="prompt" />
        <div class="image-actions">
          <button @click="generateVariations(image.image_url)">
            Generate Variations
          </button>
          <button @click="upscaleImage(image.image_url)">
            Upscale Image
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const prompt = ref('');
const style = ref('');
const aspectRatio = ref('1:1');
const quality = ref('standard');
const generating = ref(false);
const images = ref([]);

const generateImage = async () => {
  generating.value = true;
  try {
    const response = await fetch('/api/v1/images/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt: prompt.value,
        provider: 'stability_ai',
        style: style.value || undefined,
        aspect_ratio: aspectRatio.value,
        quality: quality.value
      })
    });
    
    const result = await response.json();
    images.value = result.images;
  } catch (error) {
    console.error('Image generation failed:', error);
  } finally {
    generating.value = false;
  }
};

const generateVariations = async (imageUrl) => {
  try {
    const response = await fetch('/api/v1/images/variations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source_image_url: imageUrl,
        provider: 'stability_ai',
        variation_strength: 0.7,
        num_variations: 4
      })
    });
    
    const result = await response.json();
    images.value = [...images.value, ...result.images];
  } catch (error) {
    console.error('Image variation failed:', error);
  }
};

const upscaleImage = async (imageUrl) => {
  try {
    const response = await fetch('/api/v1/images/upscale', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source_image_url: imageUrl,
        provider: 'stability_ai',
        scale_factor: 2.0,
        quality: 'high'
      })
    });
    
    const result = await response.json();
    images.value = [...images.value, ...result.images];
  } catch (error) {
    console.error('Image upscaling failed:', error);
  }
};
</script>
```

## Best Practices

### 1. Prompt Engineering
- **Be Specific**: Use detailed, descriptive prompts
- **Include Style**: Specify the desired artistic style
- **Add Quality Keywords**: Use terms like "high quality", "detailed", "professional"
- **Use Negative Prompts**: Specify what you don't want to see

### 2. Performance Optimization
- **Use Appropriate Quality**: Choose quality level based on use case
- **Batch Operations**: Use async jobs for multiple images
- **Cache Results**: Store generated images for reuse
- **Monitor Costs**: Track usage and costs

### 3. Error Handling
- **Handle Rate Limits**: Implement exponential backoff
- **Validate Inputs**: Check image URLs and parameters
- **Provide Feedback**: Show progress and error messages
- **Retry Logic**: Implement retry for transient failures

### 4. Security
- **Validate Content**: Check for inappropriate content
- **Secure API Keys**: Never expose API keys in frontend
- **Rate Limiting**: Implement client-side rate limiting
- **Content Policy**: Respect provider content policies

## Environment Variables

Configure image providers using environment variables:

```bash
# Stability AI
STABILITY_AI_API_KEY=sk-...
STABILITY_AI_DEFAULT_MODEL=stable-diffusion-xl-1024-v1-0
STABILITY_AI_BASE_URL=https://api.stability.ai
```

## Troubleshooting

### Common Issues

1. **No Providers Configured**
   - Error: "No image providers configured"
   - Solution: Configure at least one provider using `/api/v1/images/providers/configure`

2. **Invalid API Key**
   - Error: "Invalid API key for the specified provider"
   - Solution: Verify API key is correct and has proper permissions

3. **Rate Limit Exceeded**
   - Error: "Rate limit exceeded"
   - Solution: Implement exponential backoff or switch providers

4. **Content Policy Violation**
   - Error: "Content violates policy"
   - Solution: Modify prompt to comply with provider policies

5. **Image Generation Failed**
   - Error: "No images generated successfully"
   - Solution: Check prompt quality and provider status

### Debug Endpoints

- **Provider Health**: `GET /api/v1/images/providers/health`
- **Provider List**: `GET /api/v1/images/providers`
- **Job Status**: `GET /api/v1/images/jobs/{job_id}`

## Support

For additional support or questions about the Image Generation system:

1. Check the API documentation at `/docs`
2. Review the OpenAPI specification at `/openapi.json`
3. Monitor the health endpoints for real-time status
4. Check logs for detailed error information
5. Refer to provider-specific documentation for advanced features

