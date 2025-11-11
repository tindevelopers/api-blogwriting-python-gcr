# Platform Integrations Guide

This guide explains how to use the new platform integrations for publishing blog content to Webflow, Shopify, WordPress, and managing media storage with Cloudinary and Cloudflare R2.

## Table of Contents

1. [Overview](#overview)
2. [Platform Integrations](#platform-integrations)
3. [Media Storage](#media-storage)
4. [API Endpoints](#api-endpoints)
5. [Configuration](#configuration)
6. [Examples](#examples)
7. [Error Handling](#error-handling)

## Overview

The Blog Writer SDK now supports direct publishing to popular content management platforms and media storage services:

- **🌐 Webflow**: CMS publishing with collection management
- **🛒 Shopify**: Blog publishing with product recommendations
- **📝 WordPress**: REST API publishing with category management
- **☁️ Cloudinary**: Image optimization and CDN delivery
- **🚀 Cloudflare R2**: S3-compatible object storage

## Platform Integrations

### Webflow Integration

Publish blog posts directly to Webflow CMS with automatic collection management and media uploads.

#### Features
- Automatic collection item creation
- SEO metadata management
- Media upload and management
- Slug generation with timestamps
- Content formatting for Webflow

#### Configuration
```bash
WEBFLOW_API_TOKEN=your_webflow_api_token
WEBFLOW_SITE_ID=your_webflow_site_id
WEBFLOW_COLLECTION_ID=your_webflow_collection_id
```

#### API Usage
```python
# Publish to Webflow
POST /api/v1/publish/webflow
{
    "blog_result": {
        "title": "Your Blog Title",
        "content": "Your blog content...",
        "keywords": ["keyword1", "keyword2"]
    },
    "platform": "webflow",
    "publish": true,
    "media_files": [
        {
            "data": "base64_encoded_image_data",
            "filename": "image.jpg",
            "alt_text": "Image description"
        }
    ]
}
```

### Shopify Integration

Publish blog posts to Shopify with automatic product recommendations based on content keywords.

#### Features
- Blog post creation via Shopify Admin API
- Automatic product recommendations
- Category and tag management
- Media upload to Shopify assets
- SEO metadata handling

#### Configuration
```bash
SHOPIFY_SHOP_DOMAIN=your-shop.myshopify.com
SHOPIFY_ACCESS_TOKEN=your_shopify_access_token
SHOPIFY_BLOG_ID=your_shopify_blog_id
```

#### API Usage
```python
# Publish to Shopify with product recommendations
POST /api/v1/publish/shopify
{
    "blog_result": {
        "title": "Product Review Blog",
        "content": "Review content...",
        "keywords": ["product", "review", "recommendation"]
    },
    "platform": "shopify",
    "publish": true,
    "categories": ["Reviews", "Products"]
}
```

### WordPress Integration

Publish blog posts to WordPress via REST API with automatic category and tag management.

#### Features
- WordPress REST API integration
- Automatic category and tag creation
- Media upload to WordPress media library
- Featured image support
- SEO metadata management

#### Configuration
```bash
WORDPRESS_SITE_URL=https://yoursite.com
WORDPRESS_USERNAME=your_wordpress_username
WORDPRESS_APP_PASSWORD=your_wordpress_app_password
```

#### API Usage
```python
# Publish to WordPress
POST /api/v1/publish/wordpress
{
    "blog_result": {
        "title": "WordPress Blog Post",
        "content": "Your content...",
        "keywords": ["wordpress", "blog"]
    },
    "platform": "wordpress",
    "publish": true,
    "categories": ["Technology", "Blogging"],
    "media_files": [
        {
            "data": "base64_encoded_image_data",
            "filename": "featured-image.jpg",
            "alt_text": "Featured image",
            "caption": "Image caption"
        }
    ]
}
```

## Media Storage

### Cloudinary Storage

Upload and optimize images with automatic transformations and CDN delivery.

#### Features
- Automatic image optimization
- Responsive image transformations
- CDN delivery
- Format conversion (auto WebP/AVIF)
- Quality optimization

#### Configuration
```bash
CLOUDINARY_CLOUD_NAME=your_cloudinary_cloud_name
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret
CLOUDINARY_FOLDER=blog-content
```

#### API Usage
```python
# Upload to Cloudinary
POST /api/v1/media/upload/cloudinary
{
    "media_data": "base64_encoded_image_data",
    "filename": "blog-image.jpg",
    "folder": "blog-content/2024",
    "alt_text": "Blog image description",
    "metadata": {
        "author": "AI Content Generator",
        "blog_id": "123"
    }
}
```

### Cloudflare R2 Storage

S3-compatible object storage with global CDN distribution.

#### Features
- S3-compatible API
- Global CDN distribution
- Custom domain support
- Automatic folder organization
- Cost-effective storage

#### Configuration
```bash
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id
CLOUDFLARE_R2_ACCESS_KEY_ID=your_r2_access_key_id
CLOUDFLARE_R2_SECRET_ACCESS_KEY=your_r2_secret_access_key
CLOUDFLARE_R2_BUCKET_NAME=your_r2_bucket_name
CLOUDFLARE_R2_CUSTOM_DOMAIN=your_custom_domain.com
```

#### API Usage
```python
# Upload to Cloudflare R2
POST /api/v1/media/upload/cloudflare
{
    "media_data": "base64_encoded_image_data",
    "filename": "blog-video.mp4",
    "folder": "videos/blog-content",
    "metadata": {
        "content_type": "video/mp4",
        "duration": "120"
    }
}
```

## API Endpoints

### Platform Publishing Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/publish/webflow` | POST | Publish blog to Webflow CMS |
| `/api/v1/publish/shopify` | POST | Publish blog to Shopify with recommendations |
| `/api/v1/publish/wordpress` | POST | Publish blog to WordPress |

### Media Storage Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/media/upload/cloudinary` | POST | Upload media to Cloudinary |
| `/api/v1/media/upload/cloudflare` | POST | Upload media to Cloudflare R2 |

### Platform Information Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/platforms/webflow/collections` | GET | Get Webflow collections |
| `/api/v1/platforms/shopify/blogs` | GET | Get Shopify blogs |
| `/api/v1/platforms/wordpress/categories` | GET | Get WordPress categories |

## Configuration

### Environment Variables

Add the following environment variables to your `.env` file:

```bash
# Platform Integration Configuration

# Webflow Configuration
WEBFLOW_API_TOKEN=your_webflow_api_token
WEBFLOW_SITE_ID=your_webflow_site_id
WEBFLOW_COLLECTION_ID=your_webflow_collection_id

# Shopify Configuration
SHOPIFY_SHOP_DOMAIN=your-shop.myshopify.com
SHOPIFY_ACCESS_TOKEN=your_shopify_access_token
SHOPIFY_BLOG_ID=your_shopify_blog_id

# WordPress Configuration
WORDPRESS_SITE_URL=https://yoursite.com
WORDPRESS_USERNAME=your_wordpress_username
WORDPRESS_APP_PASSWORD=your_wordpress_app_password

# Media Storage Configuration

# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME=your_cloudinary_cloud_name
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret
CLOUDINARY_FOLDER=blog-content

# Cloudflare R2 Configuration
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id
CLOUDFLARE_R2_ACCESS_KEY_ID=your_r2_access_key_id
CLOUDFLARE_R2_SECRET_ACCESS_KEY=your_r2_secret_access_key
CLOUDFLARE_R2_BUCKET_NAME=your_r2_bucket_name
CLOUDFLARE_R2_CUSTOM_DOMAIN=your_custom_domain.com
```

### Dependencies

The following dependencies are automatically installed:

```txt
cloudinary>=1.40.0
boto3>=1.34.0
botocore>=1.34.0
```

## Examples

### Complete Blog Publishing Workflow

```python
import requests
import base64

# 1. Generate blog content
blog_response = requests.post("http://localhost:8000/api/v1/blog/generate", json={
    "topic": "Best Pet Care Tips",
    "keywords": ["pet care", "tips", "health"],
    "tone": "professional",
    "length": "medium"
})

blog_result = blog_response.json()

# 2. Upload featured image to Cloudinary
with open("featured-image.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

media_response = requests.post("http://localhost:8000/api/v1/media/upload/cloudinary", json={
    "media_data": image_data,
    "filename": "featured-image.jpg",
    "folder": "blog-content/2024",
    "alt_text": "Pet care tips featured image"
})

media_result = media_response.json()

# 3. Publish to WordPress with the uploaded image
publish_response = requests.post("http://localhost:8000/api/v1/publish/wordpress", json={
    "blog_result": blog_result,
    "platform": "wordpress",
    "publish": True,
    "categories": ["Pet Care", "Health"],
    "media_files": [{
        "data": image_data,
        "filename": "featured-image.jpg",
        "alt_text": "Pet care tips featured image"
    }]
})

print("Blog published successfully:", publish_response.json())
```

### Shopify with Product Recommendations

```python
# Generate blog about pet products
blog_response = requests.post("http://localhost:8000/api/v1/blog/generate", json={
    "topic": "Best Dog Toys for Active Dogs",
    "keywords": ["dog toys", "active dogs", "exercise"],
    "tone": "informative"
})

blog_result = blog_response.json()

# Publish to Shopify (automatically includes product recommendations)
shopify_response = requests.post("http://localhost:8000/api/v1/publish/shopify", json={
    "blog_result": blog_result,
    "platform": "shopify",
    "publish": True,
    "categories": ["Dog Products", "Toys"]
})

result = shopify_response.json()
print(f"Published to Shopify with {len(result['result']['product_recommendations'])} product recommendations")
```

### Batch Media Upload

```python
import os
import base64

# Upload multiple images for a blog post
image_files = ["image1.jpg", "image2.jpg", "image3.jpg"]
uploaded_media = []

for image_file in image_files:
    with open(image_file, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()
    
    response = requests.post("http://localhost:8000/api/v1/media/upload/cloudinary", json={
        "media_data": image_data,
        "filename": image_file,
        "folder": "blog-gallery/2024",
        "alt_text": f"Blog gallery image: {image_file}"
    })
    
    uploaded_media.append(response.json()["result"])

print(f"Uploaded {len(uploaded_media)} images successfully")
```

## Error Handling

### Common Error Scenarios

1. **Missing Credentials**
   ```json
   {
     "detail": "Webflow API token is required"
   }
   ```

2. **Invalid Collection/Blog ID**
   ```json
   {
     "detail": "Webflow collection ID is required"
   }
   ```

3. **Upload Failures**
   ```json
   {
     "detail": "Failed to upload media to Cloudinary: Invalid API credentials"
   }
   ```

### Error Response Format

All endpoints return consistent error responses:

```json
{
  "detail": "Error description",
  "status_code": 500,
  "platform": "webflow"
}
```

### Retry Logic

The SDK includes automatic retry logic for:
- Network timeouts
- Rate limiting (429 errors)
- Temporary service unavailability (5xx errors)

### Fallback Mechanisms

For media storage, you can configure multiple providers with automatic fallback:

```python
from src.blog_writer_sdk.integrations import MediaStorageManager, CloudinaryStorage, CloudflareR2Storage

# Create storage manager with fallback
primary_storage = CloudinaryStorage()
fallback_storage = CloudflareR2Storage()

storage_manager = MediaStorageManager(primary_storage)
storage_manager.add_fallback_provider(fallback_storage)

# Upload with automatic fallback
result = await storage_manager.upload_media(media_data, filename)
```

## Best Practices

### 1. Environment Configuration
- Use separate API keys for development and production
- Store credentials securely using environment variables
- Test connections before deploying to production

### 2. Media Optimization
- Use Cloudinary for images that need optimization and transformations
- Use Cloudflare R2 for large files and videos
- Always include alt text for accessibility

### 3. Content Management
- Use descriptive categories and tags
- Implement proper SEO metadata
- Test publishing workflows in staging environments

### 4. Error Handling
- Implement proper error handling in your applications
- Log errors for debugging and monitoring
- Provide fallback options for failed operations

### 5. Rate Limiting
- Be aware of platform-specific rate limits
- Implement exponential backoff for retries
- Monitor usage to avoid hitting limits

## Support

For issues with platform integrations:

1. Check the API documentation at `/docs`
2. Verify your credentials and configuration
3. Review the error logs for specific details
4. Test with minimal examples first

The integrations are designed to be robust and handle common scenarios automatically, but proper configuration and error handling will ensure smooth operation in production environments.




