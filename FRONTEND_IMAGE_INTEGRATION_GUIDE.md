# Frontend Integration Guide: Image Generation for Blog Writing

**Version**: 1.2.0  
**Date**: 2025-01-10  
**API Endpoint**: `POST /api/v1/images/generate`

---

## Overview

This guide shows how to integrate Stability.ai image generation into your blog writing workflow. Images can be generated automatically based on blog topics, keywords, or user prompts, and seamlessly included in blog posts.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [API Integration](#api-integration)
3. [Workflow Integration](#workflow-integration)
4. [Image Types & Use Cases](#image-types--use-cases)
5. [Best Practices](#best-practices)
6. [Error Handling](#error-handling)
7. [Complete Examples](#complete-examples)

---

## Quick Start

### Basic Image Generation

```typescript
// Generate a featured image for a blog post
const generateBlogImage = async (topic: string, keywords: string[]) => {
  const response = await fetch('https://blog-writer-api-dev-613248238610.europe-west1.run.app/api/v1/images/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      prompt: `Professional blog post featured image: ${topic}`,
      provider: 'stability_ai',
      style: 'photographic',
      aspect_ratio: '16:9',
      quality: 'high',
      width: 1920,
      height: 1080
    })
  });

  const data = await response.json();
  return data.images[0]; // Returns GeneratedImage object
};
```

---

## API Integration

### TypeScript Types

```typescript
// Image generation request
interface ImageGenerationRequest {
  prompt: string;                    // Required: 3-1000 characters
  provider?: 'stability_ai';         // Optional: defaults to stability_ai
  style?: ImageStyle;                 // Optional: photographic, digital_art, etc.
  aspect_ratio?: ImageAspectRatio;    // Optional: 1:1, 16:9, 4:3, etc.
  quality?: ImageQuality;             // Optional: draft, standard, high, ultra
  negative_prompt?: string;            // Optional: what to avoid
  seed?: number;                      // Optional: for reproducible results
  steps?: number;                      // Optional: 10-150 (default: 30)
  guidance_scale?: number;             // Optional: 1.0-20.0 (default: 7.0)
  width?: number;                      // Optional: 64-2048
  height?: number;                     // Optional: 64-2048
  tags?: string[];                     // Optional: for categorization
}

// Image generation response
interface ImageGenerationResponse {
  success: boolean;
  images: GeneratedImage[];
  generation_time_seconds: number;
  provider: 'stability_ai';
  model: string;
  cost: number;
  request_id?: string;
  prompt_used: string;
  error_message?: string;
}

interface GeneratedImage {
  image_id: string;
  image_url?: string;                 // URL to access the image
  image_data?: string;                // Base64 encoded image
  width: number;
  height: number;
  format: string;                      // png, jpeg, etc.
  size_bytes?: number;
  seed?: number;
  steps?: number;
  guidance_scale?: number;
  created_at: string;
  expires_at?: string;
  quality_score?: number;              // 0-1
  safety_score?: number;               // 0-1
  provider: 'stability_ai';
  model?: string;
}

// Enums
type ImageStyle = 
  | 'photographic' | 'digital_art' | 'painting' | 'sketch' 
  | 'cartoon' | 'anime' | 'realistic' | 'abstract' 
  | 'minimalist' | 'vintage' | 'cyberpunk' | 'fantasy' 
  | 'sci_fi' | 'watercolor' | 'oil_painting';

type ImageAspectRatio = 
  | '1:1' | '3:4' | '4:3' | '16:9' | '21:9' | '2:3' | 'custom';

type ImageQuality = 'draft' | 'standard' | 'high' | 'ultra';
```

### API Client Function

```typescript
class BlogImageGenerator {
  private apiUrl: string;

  constructor(apiUrl: string = 'https://blog-writer-api-dev-613248238610.europe-west1.run.app') {
    this.apiUrl = apiUrl;
  }

  /**
   * Generate an image from a text prompt
   */
  async generateImage(request: ImageGenerationRequest): Promise<ImageGenerationResponse> {
    const response = await fetch(`${this.apiUrl}/api/v1/images/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        provider: 'stability_ai',
        ...request
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Image generation failed: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Generate a featured image for a blog post
   */
  async generateFeaturedImage(
    topic: string,
    keywords: string[] = [],
    options: Partial<ImageGenerationRequest> = {}
  ): Promise<GeneratedImage> {
    // Build prompt from topic and keywords
    const keywordText = keywords.length > 0 ? ` featuring ${keywords.slice(0, 3).join(', ')}` : '';
    const prompt = `Professional blog post featured image: ${topic}${keywordText}, high quality, modern design`;

    const response = await await this.generateImage({
      prompt,
      style: 'photographic',
      aspect_ratio: '16:9',
      quality: 'high',
      width: 1920,
      height: 1080,
      negative_prompt: 'blurry, low quality, watermark, text overlay',
      ...options
    });

    if (!response.success || response.images.length === 0) {
      throw new Error(response.error_message || 'Failed to generate image');
    }

    return response.images[0];
  }

  /**
   * Generate multiple image variations
   */
  async generateVariations(
    sourceImageUrl: string,
    numVariations: number = 4,
    variationStrength: number = 0.7
  ): Promise<ImageGenerationResponse> {
    const response = await fetch(`${this.apiUrl}/api/v1/images/variations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source_image_url: sourceImageUrl,
        provider: 'stability_ai',
        num_variations: numVariations,
        variation_strength: variationStrength
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Variation generation failed');
    }

    return await response.json();
  }

  /**
   * Upscale an image
   */
  async upscaleImage(
    sourceImageUrl: string,
    scaleFactor: number = 2.0
  ): Promise<ImageGenerationResponse> {
    const response = await fetch(`${this.apiUrl}/api/v1/images/upscale`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source_image_url: sourceImageUrl,
        provider: 'stability_ai',
        scale_factor: scaleFactor,
        quality: 'high'
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Image upscaling failed');
    }

    return await response.json();
  }

  /**
   * Check provider status
   */
  async checkProviderStatus(): Promise<Record<string, any>> {
    const response = await fetch(`${this.apiUrl}/api/v1/images/providers`);
    if (!response.ok) {
      throw new Error('Failed to check provider status');
    }
    return await response.json();
  }
}
```

---

## Workflow Integration

### 1. Generate Image During Blog Research

```typescript
// Integrate image generation into blog research workflow
async function performBlogResearch(topic: string, keywords: string[]) {
  // Step 1: Research keywords and content
  const keywordAnalysis = await analyzeKeywords(topic, keywords);
  
  // Step 2: Generate featured image in parallel
  const imagePromise = imageGenerator.generateFeaturedImage(topic, keywords, {
    style: 'photographic',
    quality: 'high'
  });

  // Step 3: Generate blog content
  const blogContent = await generateBlogContent(topic, keywords);

  // Step 4: Wait for image and attach to blog
  const featuredImage = await imagePromise;
  
  return {
    ...blogContent,
    featured_image: {
      url: featuredImage.image_url,
      alt_text: `Featured image for ${topic}`,
      width: featuredImage.width,
      height: featuredImage.height
    }
  };
}
```

### 2. Generate Images for Blog Sections

```typescript
// Generate images for different blog sections
async function generateBlogWithImages(topic: string, keywords: string[]) {
  const sections = [
    { title: 'Introduction', keywords: keywords.slice(0, 2) },
    { title: 'Main Content', keywords: keywords.slice(2, 5) },
    { title: 'Conclusion', keywords: keywords.slice(5, 7) }
  ];

  // Generate images for each section
  const sectionImages = await Promise.all(
    sections.map(async (section) => {
      try {
        const image = await imageGenerator.generateImage({
          prompt: `Illustration for blog section: ${section.title} about ${topic}`,
          style: 'digital_art',
          aspect_ratio: '4:3',
          quality: 'standard',
          width: 1200,
          height: 900
        });
        return {
          section: section.title,
          image: image.images[0]
        };
      } catch (error) {
        console.warn(`Failed to generate image for ${section.title}:`, error);
        return null;
      }
    })
  );

  // Filter out failed generations
  return sectionImages.filter(img => img !== null);
}
```

### 3. React Hook for Image Generation

```typescript
import { useState, useCallback } from 'react';

interface UseImageGenerationReturn {
  generating: boolean;
  image: GeneratedImage | null;
  error: string | null;
  generateImage: (request: ImageGenerationRequest) => Promise<void>;
  generateFeaturedImage: (topic: string, keywords?: string[]) => Promise<void>;
  reset: () => void;
}

export function useImageGeneration(apiUrl?: string): UseImageGenerationReturn {
  const [generating, setGenerating] = useState(false);
  const [image, setImage] = useState<GeneratedImage | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const generator = new BlogImageGenerator(apiUrl);

  const generateImage = useCallback(async (request: ImageGenerationRequest) => {
    setGenerating(true);
    setError(null);
    try {
      const response = await generator.generateImage(request);
      if (response.success && response.images.length > 0) {
        setImage(response.images[0]);
      } else {
        throw new Error(response.error_message || 'Image generation failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setImage(null);
    } finally {
      setGenerating(false);
    }
  }, [apiUrl]);

  const generateFeaturedImage = useCallback(async (topic: string, keywords: string[] = []) => {
    setGenerating(true);
    setError(null);
    try {
      const image = await generator.generateFeaturedImage(topic, keywords);
      setImage(image);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setImage(null);
    } finally {
      setGenerating(false);
    }
  }, [apiUrl]);

  const reset = useCallback(() => {
    setImage(null);
    setError(null);
    setGenerating(false);
  }, []);

  return {
    generating,
    image,
    error,
    generateImage,
    generateFeaturedImage,
    reset
  };
}
```

### 4. React Component Example

```typescript
import React, { useState } from 'react';
import { useImageGeneration } from './hooks/useImageGeneration';

interface BlogImageGeneratorProps {
  topic: string;
  keywords: string[];
  onImageGenerated: (image: GeneratedImage) => void;
}

export function BlogImageGenerator({ topic, keywords, onImageGenerated }: BlogImageGeneratorProps) {
  const { generating, image, error, generateFeaturedImage } = useImageGeneration();
  const [customPrompt, setCustomPrompt] = useState('');

  const handleGenerate = async () => {
    const prompt = customPrompt || `Professional blog post featured image: ${topic}`;
    await generateFeaturedImage(prompt, keywords);
  };

  React.useEffect(() => {
    if (image) {
      onImageGenerated(image);
    }
  }, [image, onImageGenerated]);

  return (
    <div className="blog-image-generator">
      <div className="generator-controls">
        <input
          type="text"
          value={customPrompt}
          onChange={(e) => setCustomPrompt(e.target.value)}
          placeholder="Custom image prompt (optional)"
          className="prompt-input"
        />
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="generate-button"
        >
          {generating ? 'Generating...' : 'Generate Featured Image'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      {image && (
        <div className="generated-image-preview">
          <img
            src={image.image_url || `data:image/${image.format};base64,${image.image_data}`}
            alt={`Generated image for ${topic}`}
            className="preview-image"
          />
          <div className="image-info">
            <p>Size: {image.width} × {image.height}px</p>
            {image.quality_score && (
              <p>Quality Score: {(image.quality_score * 100).toFixed(0)}%</p>
            )}
          </div>
        </div>
      )}

      {generating && (
        <div className="loading-indicator">
          <div className="spinner" />
          <p>Generating image... This may take 10-30 seconds</p>
        </div>
      )}
    </div>
  );
}
```

---

## Image Types & Use Cases

### 1. Featured Images

**Use Case**: Main hero image for blog posts

```typescript
const featuredImage = await imageGenerator.generateFeaturedImage(
  'How to Groom German Shepherds',
  ['pet care', 'dog grooming', 'german shepherd'],
  {
    style: 'photographic',
    aspect_ratio: '16:9',
    quality: 'high',
    width: 1920,
    height: 1080,
    negative_prompt: 'text overlay, watermark, blurry'
  }
);
```

### 2. Section Illustrations

**Use Case**: Images for blog sections or headers

```typescript
const sectionImage = await imageGenerator.generateImage({
  prompt: 'Illustration showing proper dog grooming technique',
  style: 'digital_art',
  aspect_ratio: '4:3',
  quality: 'standard',
  width: 1200,
  height: 900
});
```

### 3. Social Media Images

**Use Case**: Square images for social sharing

```typescript
const socialImage = await imageGenerator.generateImage({
  prompt: 'Social media image: How to Groom German Shepherds',
  style: 'minimalist',
  aspect_ratio: '1:1',
  quality: 'high',
  width: 1080,
  height: 1080
});
```

### 4. Infographic Elements

**Use Case**: Visual elements for data or step-by-step guides

```typescript
const infographicImage = await imageGenerator.generateImage({
  prompt: 'Clean infographic style illustration: Dog grooming steps',
  style: 'minimalist',
  aspect_ratio: '16:9',
  quality: 'high',
  negative_prompt: 'photorealistic, complex background'
});
```

---

## Best Practices

### 1. Prompt Engineering

**✅ Good Prompts:**
```typescript
// Specific and descriptive
"Professional blog post featured image: German Shepherd dog being groomed, clean background, high quality"

// Include style and quality
"Modern minimalist illustration: Pet care tips, clean design, professional"

// Use keywords naturally
"Blog header image featuring: ${keywords.join(', ')}, professional photography style"
```

**❌ Bad Prompts:**
```typescript
// Too vague
"dog"

// Too complex
"A very detailed image of a dog that is being groomed with many tools and products in a professional setting with lots of details and colors and..."

// Includes unwanted elements
"German Shepherd with text overlay and watermark"
```

### 2. Image Caching

```typescript
// Cache generated images to avoid regenerating
const imageCache = new Map<string, GeneratedImage>();

async function getCachedOrGenerate(
  cacheKey: string,
  generator: () => Promise<GeneratedImage>
): Promise<GeneratedImage> {
  if (imageCache.has(cacheKey)) {
    return imageCache.get(cacheKey)!;
  }
  
  const image = await generator();
  imageCache.set(cacheKey, image);
  return image;
}

// Usage
const image = await getCachedOrGenerate(
  `featured-${topic}-${keywords.join('-')}`,
  () => imageGenerator.generateFeaturedImage(topic, keywords)
);
```

### 3. Error Handling & Fallbacks

```typescript
async function generateImageWithFallback(
  primaryPrompt: string,
  fallbackPrompt: string
): Promise<GeneratedImage | null> {
  try {
    // Try primary prompt
    const response = await imageGenerator.generateImage({
      prompt: primaryPrompt,
      quality: 'high'
    });
    return response.images[0];
  } catch (error) {
    console.warn('Primary image generation failed, trying fallback:', error);
    
    try {
      // Try simpler fallback
      const response = await imageGenerator.generateImage({
        prompt: fallbackPrompt,
        quality: 'standard'
      });
      return response.images[0];
    } catch (fallbackError) {
      console.error('Fallback image generation also failed:', fallbackError);
      return null;
    }
  }
}
```

### 4. Loading States & User Feedback

```typescript
// Show progress for long-running operations
const [progress, setProgress] = useState(0);

async function generateWithProgress() {
  setProgress(0);
  
  // Simulate progress (actual API doesn't support progress, but you can estimate)
  const progressInterval = setInterval(() => {
    setProgress(prev => Math.min(prev + 5, 90));
  }, 500);
  
  try {
    const image = await imageGenerator.generateFeaturedImage(topic, keywords);
    clearInterval(progressInterval);
    setProgress(100);
    return image;
  } catch (error) {
    clearInterval(progressInterval);
    setProgress(0);
    throw error;
  }
}
```

### 5. Image Optimization

```typescript
// Optimize images before uploading to CMS
async function optimizeImageForWeb(image: GeneratedImage): Promise<Blob> {
  // If image_data is base64, convert to blob
  if (image.image_data) {
    const base64Data = image.image_data.replace(/^data:image\/\w+;base64,/, '');
    const binaryData = atob(base64Data);
    const bytes = new Uint8Array(binaryData.length);
    
    for (let i = 0; i < binaryData.length; i++) {
      bytes[i] = binaryData.charCodeAt(i);
    }
    
    return new Blob([bytes], { type: `image/${image.format}` });
  }
  
  // If image_url, fetch and convert
  if (image.image_url) {
    const response = await fetch(image.image_url);
    return await response.blob();
  }
  
  throw new Error('No image data available');
}
```

---

## Error Handling

### Common Errors & Solutions

```typescript
interface ImageGenerationError {
  code: string;
  message: string;
  retryable: boolean;
}

function handleImageGenerationError(error: any): ImageGenerationError {
  // Rate limit
  if (error.message?.includes('429') || error.message?.includes('rate limit')) {
    return {
      code: 'RATE_LIMIT',
      message: 'Too many requests. Please wait a moment and try again.',
      retryable: true
    };
  }
  
  // Invalid API key
  if (error.message?.includes('401') || error.message?.includes('unauthorized')) {
    return {
      code: 'AUTH_ERROR',
      message: 'Image generation service is not configured. Please contact support.',
      retryable: false
    };
  }
  
  // Content policy violation
  if (error.message?.includes('content policy') || error.message?.includes('policy')) {
    return {
      code: 'CONTENT_POLICY',
      message: 'Image prompt violates content policy. Please modify your prompt.',
      retryable: false
    };
  }
  
  // Quota exceeded
  if (error.message?.includes('402') || error.message?.includes('quota')) {
    return {
      code: 'QUOTA_EXCEEDED',
      message: 'Image generation quota exceeded. Please upgrade your plan.',
      retryable: false
    };
  }
  
  // Generic error
  return {
    code: 'UNKNOWN',
    message: error.message || 'Failed to generate image. Please try again.',
    retryable: true
  };
}

// Usage with retry logic
async function generateImageWithRetry(
  request: ImageGenerationRequest,
  maxRetries: number = 3
): Promise<GeneratedImage> {
  let lastError: ImageGenerationError | null = null;
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await imageGenerator.generateImage(request);
      return response.images[0];
    } catch (error) {
      lastError = handleImageGenerationError(error);
      
      if (!lastError.retryable) {
        throw new Error(lastError.message);
      }
      
      // Exponential backoff
      await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
    }
  }
  
  throw new Error(lastError?.message || 'Failed to generate image after retries');
}
```

---

## Complete Examples

### Example 1: Full Blog Post with Images

```typescript
interface BlogPostWithImages {
  title: string;
  content: string;
  featured_image: GeneratedImage;
  section_images: Array<{
    section: string;
    image: GeneratedImage;
  }>;
}

async function generateCompleteBlogPost(
  topic: string,
  keywords: string[]
): Promise<BlogPostWithImages> {
  // Step 1: Generate blog content
  const blogContent = await generateBlogContent(topic, keywords);
  
  // Step 2: Generate featured image
  const featuredImage = await imageGenerator.generateFeaturedImage(topic, keywords);
  
  // Step 3: Generate section images (optional, can be done in parallel)
  const sections = extractSections(blogContent.content);
  const sectionImages = await Promise.all(
    sections.map(async (section, index) => {
      try {
        const image = await imageGenerator.generateImage({
          prompt: `Illustration for blog section ${index + 1}: ${section.title}`,
          style: 'digital_art',
          aspect_ratio: '4:3',
          quality: 'standard'
        });
        return {
          section: section.title,
          image: image.images[0]
        };
      } catch (error) {
        console.warn(`Failed to generate image for section ${section.title}`);
        return null;
      }
    })
  );
  
  return {
    title: blogContent.title,
    content: blogContent.content,
    featured_image: featuredImage,
    section_images: sectionImages.filter(img => img !== null) as any[]
  };
}
```

### Example 2: Image Gallery Component

```typescript
import React, { useState } from 'react';

interface ImageGalleryProps {
  topic: string;
  keywords: string[];
}

export function ImageGallery({ topic, keywords }: ImageGalleryProps) {
  const [images, setImages] = useState<GeneratedImage[]>([]);
  const [generating, setGenerating] = useState(false);
  
  const generateGallery = async () => {
    setGenerating(true);
    try {
      // Generate multiple images with different styles
      const styles: ImageStyle[] = ['photographic', 'digital_art', 'minimalist'];
      
      const imagePromises = styles.map(style =>
        imageGenerator.generateImage({
          prompt: `Blog image: ${topic}`,
          style,
          aspect_ratio: '16:9',
          quality: 'high'
        })
      );
      
      const responses = await Promise.all(imagePromises);
      const allImages = responses.flatMap(r => r.images);
      setImages(allImages);
    } catch (error) {
      console.error('Failed to generate gallery:', error);
    } finally {
      setGenerating(false);
    }
  };
  
  return (
    <div className="image-gallery">
      <button onClick={generateGallery} disabled={generating}>
        {generating ? 'Generating...' : 'Generate Image Gallery'}
      </button>
      
      <div className="gallery-grid">
        {images.map((image) => (
          <div key={image.image_id} className="gallery-item">
            <img
              src={image.image_url || `data:image/${image.format};base64,${image.image_data}`}
              alt={`Generated image for ${topic}`}
            />
            <div className="image-meta">
              <span>{image.width} × {image.height}</span>
              {image.quality_score && (
                <span>Quality: {(image.quality_score * 100).toFixed(0)}%</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### Example 3: Integration with Blog Publishing

```typescript
async function publishBlogWithImages(
  blogPost: BlogPost,
  images: GeneratedImage[]
): Promise<PublishResult> {
  // Step 1: Upload images to CMS/media storage
  const uploadedImages = await Promise.all(
    images.map(async (image) => {
      const imageBlob = await optimizeImageForWeb(image);
      const uploadedUrl = await uploadToCMS(imageBlob, {
        filename: `blog-${blogPost.id}-${image.image_id}.${image.format}`,
        alt_text: `Image for ${blogPost.title}`
      });
      return {
        ...image,
        cms_url: uploadedUrl
      };
    })
  );
  
  // Step 2: Insert images into blog content
  const contentWithImages = insertImagesIntoContent(
    blogPost.content,
    uploadedImages
  );
  
  // Step 3: Publish blog post with images
  const publishResult = await publishToCMS({
    ...blogPost,
    content: contentWithImages,
    featured_image: uploadedImages[0]?.cms_url,
    images: uploadedImages.map(img => img.cms_url)
  });
  
  return publishResult;
}

function insertImagesIntoContent(
  content: string,
  images: GeneratedImage[]
): string {
  // Simple implementation: insert images at section breaks
  const sections = content.split('\n\n');
  const imagesToInsert = images.slice(1); // Skip featured image
  
  let imageIndex = 0;
  return sections.map((section, index) => {
    // Insert image every 2-3 sections
    if (index > 0 && index % 3 === 0 && imageIndex < imagesToInsert.length) {
      const image = imagesToInsert[imageIndex++];
      return `${section}\n\n![${image.image_id}](${image.image_url || image.image_data})\n\n`;
    }
    return section;
  }).join('\n\n');
}
```

---

## Summary

### Key Points

1. **API Endpoint**: `POST /api/v1/images/generate`
2. **Default Provider**: Stability.ai (no need to specify)
3. **Required Field**: `prompt` (3-1000 characters)
4. **Response**: Returns `ImageGenerationResponse` with `images` array
5. **Error Handling**: Check `success` field and `error_message` if failed

### Quick Checklist

- [ ] Stability.ai API key configured in Secret Manager
- [ ] Image generation endpoint accessible
- [ ] Error handling implemented
- [ ] Loading states shown to users
- [ ] Images cached to avoid regeneration
- [ ] Images optimized before upload
- [ ] Fallback images for failed generations
- [ ] Alt text and metadata included

### Next Steps

1. **Test Image Generation**: Use the API endpoint directly
2. **Integrate into Workflow**: Add image generation to blog creation flow
3. **Add UI Components**: Create React components for image generation
4. **Optimize Performance**: Implement caching and parallel generation
5. **Handle Errors**: Add comprehensive error handling and retries

---

## Additional Resources

- **API Documentation**: See `IMAGE_GENERATION_GUIDE.md`
- **API Endpoints**: `/docs` endpoint for interactive API documentation
- **Provider Status**: `GET /api/v1/images/providers` to check configuration
- **Health Check**: `GET /api/v1/images/providers/health` for provider status

---

**Need Help?** Check the API documentation at `/docs` or review error messages for specific guidance.

