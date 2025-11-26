"""
Media storage integrations for the Blog Writer SDK.

This module provides integrations with various media storage services
like Cloudinary, Cloudflare R2, and AWS S3 for storing and managing
blog-related media assets.
"""

import os
import logging
import httpx
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import base64
import json
from abc import ABC, abstractmethod

from ..models.blog_models import BlogPost, BlogGenerationResult


class MediaStorageProvider(ABC):
    """Abstract base class for media storage providers."""
    
    @abstractmethod
    async def upload_media(
        self, 
        media_data: bytes, 
        filename: str,
        folder: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Upload media to storage provider."""
        pass
    
    @abstractmethod
    async def get_media_url(self, media_id: str) -> str:
        """Get public URL for media."""
        pass
    
    @abstractmethod
    async def delete_media(self, media_id: str) -> bool:
        """Delete media from storage."""
        pass


class CloudinaryStorage(MediaStorageProvider):
    """
    Cloudinary media storage provider.
    
    Handles image and video uploads to Cloudinary with automatic
    optimization, transformations, and CDN delivery.
    """
    
    def __init__(
        self,
        cloud_name: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        default_folder: Optional[str] = None,
    ):
        """
        Initialize Cloudinary storage.
        
        Args:
            cloud_name: Cloudinary cloud name
            api_key: Cloudinary API key
            api_secret: Cloudinary API secret
            default_folder: Default folder for uploads
        """
        self.cloud_name = cloud_name or os.getenv("CLOUDINARY_CLOUD_NAME")
        self.api_key = api_key or os.getenv("CLOUDINARY_API_KEY")
        self.api_secret = api_secret or os.getenv("CLOUDINARY_API_SECRET")
        self.default_folder = default_folder or os.getenv("CLOUDINARY_FOLDER", "blog-content")
        
        if not all([self.cloud_name, self.api_key, self.api_secret]):
            raise ValueError("Cloudinary cloud_name, api_key, and api_secret are required")
        
        self.upload_url = f"https://api.cloudinary.com/v1_1/{self.cloud_name}/image/upload"
        self.logger = logging.getLogger(__name__)
    
    async def upload_media(
        self, 
        media_data: bytes, 
        filename: str,
        folder: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload media to Cloudinary.
        
        Args:
            media_data: Media file data
            filename: Original filename
            folder: Upload folder (overrides default)
            metadata: Additional metadata
            
        Returns:
            Dictionary containing upload details
        """
        try:
            import cloudinary
            import cloudinary.uploader
            
            # Configure Cloudinary
            cloudinary.config(
                cloud_name=self.cloud_name,
                api_key=self.api_key,
                api_secret=self.api_secret
            )
            
            # Prepare upload options
            upload_options = {
                "folder": folder or self.default_folder,
                "public_id": self._generate_public_id(filename),
                "resource_type": "auto",  # Auto-detect image/video/raw
                "quality": "auto",
                "fetch_format": "auto"
            }
            
            # Add metadata if provided
            if metadata:
                upload_options.update(metadata)
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                media_data,
                **upload_options
            )
            
            self.logger.info(f"Uploaded media to Cloudinary: {result['public_id']}")
            
            return {
                "id": result["public_id"],
                "url": result["secure_url"],
                "width": result.get("width"),
                "height": result.get("height"),
                "format": result.get("format"),
                "size": result.get("bytes"),
                "created_at": result.get("created_at"),
                "transformation_url": self._get_transformation_url(result["public_id"])
            }
            
        except Exception as e:
            self.logger.error(f"Failed to upload media to Cloudinary: {str(e)}")
            raise
    
    async def get_media_url(self, media_id: str, transformations: Optional[Dict[str, Any]] = None) -> str:
        """
        Get public URL for media with optional transformations.
        
        Args:
            media_id: Cloudinary public ID
            transformations: Image/video transformations
            
        Returns:
            Public URL
        """
        try:
            import cloudinary.utils
            
            if transformations:
                return cloudinary.utils.cloudinary_url(media_id, **transformations)[0]
            else:
                return cloudinary.utils.cloudinary_url(media_id)[0]
                
        except Exception as e:
            self.logger.error(f"Failed to get Cloudinary URL: {str(e)}")
            raise
    
    async def delete_media(self, media_id: str) -> bool:
        """
        Delete media from Cloudinary.
        
        Args:
            media_id: Cloudinary public ID
            
        Returns:
            True if successful
        """
        try:
            import cloudinary.uploader
            
            result = cloudinary.uploader.destroy(media_id)
            
            if result.get("result") == "ok":
                self.logger.info(f"Deleted media from Cloudinary: {media_id}")
                return True
            else:
                self.logger.warning(f"Failed to delete Cloudinary media: {media_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to delete Cloudinary media: {str(e)}")
            return False
    
    def _generate_public_id(self, filename: str) -> str:
        """Generate Cloudinary public ID from filename."""
        import re
        from datetime import datetime
        
        # Remove extension and clean filename
        name = filename.rsplit('.', 1)[0] if '.' in filename else filename
        name = re.sub(r'[^\w\-_]', '_', name.lower())
        
        # Add timestamp for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return f"{name}_{timestamp}"
    
    def _get_transformation_url(self, public_id: str) -> str:
        """Get URL with common transformations for blog content."""
        return f"https://res.cloudinary.com/{self.cloud_name}/image/upload/w_auto,h_auto,c_fill,q_auto,f_auto/{public_id}"


class CloudflareR2Storage(MediaStorageProvider):
    """
    Cloudflare R2 media storage provider.
    
    Handles file uploads to Cloudflare R2 with S3-compatible API.
    """
    
    def __init__(
        self,
        account_id: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        bucket_name: Optional[str] = None,
        custom_domain: Optional[str] = None,
    ):
        """
        Initialize Cloudflare R2 storage.
        
        Args:
            account_id: Cloudflare account ID
            access_key_id: R2 access key ID
            secret_access_key: R2 secret access key
            bucket_name: R2 bucket name
            custom_domain: Custom domain for R2 bucket
        """
        self.account_id = account_id or os.getenv("CLOUDFLARE_ACCOUNT_ID")
        self.access_key_id = access_key_id or os.getenv("CLOUDFLARE_R2_ACCESS_KEY_ID")
        self.secret_access_key = secret_access_key or os.getenv("CLOUDFLARE_R2_SECRET_ACCESS_KEY")
        self.bucket_name = bucket_name or os.getenv("CLOUDFLARE_R2_BUCKET_NAME")
        self.custom_domain = custom_domain or os.getenv("CLOUDFLARE_R2_CUSTOM_DOMAIN")
        
        if not all([self.access_key_id, self.secret_access_key, self.bucket_name]):
            raise ValueError("Cloudflare R2 access_key_id, secret_access_key, and bucket_name are required")
        
        # R2 endpoint
        self.endpoint_url = f"https://{self.account_id}.r2.cloudflarestorage.com"
        
        self.logger = logging.getLogger(__name__)
    
    async def upload_media(
        self, 
        media_data: bytes, 
        filename: str,
        folder: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload media to Cloudflare R2.
        
        Args:
            media_data: Media file data
            filename: Original filename
            folder: Upload folder
            metadata: Additional metadata
            
        Returns:
            Dictionary containing upload details
        """
        try:
            import boto3
            from botocore.client import Config
            
            # Create S3 client for R2
            s3_client = boto3.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                config=Config(signature_version='s3v4')
            )
            
            # Generate key
            timestamp = datetime.now().strftime("%Y/%m/%d")
            key = f"{folder or 'blog-media'}/{timestamp}/{filename}"
            
            # Upload to R2
            s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=media_data,
                ContentType=self._get_content_type(filename),
                Metadata=metadata or {}
            )
            
            # Generate public URL
            if self.custom_domain:
                public_url = f"https://{self.custom_domain}/{key}"
            else:
                public_url = f"https://{self.bucket_name}.r2.cloudflarestorage.com/{key}"
            
            self.logger.info(f"Uploaded media to Cloudflare R2: {key}")
            
            return {
                "id": key,
                "url": public_url,
                "bucket": self.bucket_name,
                "key": key,
                "size": len(media_data),
                "content_type": self._get_content_type(filename),
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to upload media to Cloudflare R2: {str(e)}")
            raise
    
    async def get_media_url(self, media_id: str) -> str:
        """
        Get public URL for media.
        
        Args:
            media_id: R2 object key
            
        Returns:
            Public URL
        """
        if self.custom_domain:
            return f"https://{self.custom_domain}/{media_id}"
        else:
            return f"https://{self.bucket_name}.r2.cloudflarestorage.com/{media_id}"
    
    async def delete_media(self, media_id: str) -> bool:
        """
        Delete media from Cloudflare R2.
        
        Args:
            media_id: R2 object key
            
        Returns:
            True if successful
        """
        try:
            import boto3
            from botocore.client import Config
            
            # Create S3 client for R2
            s3_client = boto3.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                config=Config(signature_version='s3v4')
            )
            
            # Delete object
            s3_client.delete_object(Bucket=self.bucket_name, Key=media_id)
            
            self.logger.info(f"Deleted media from Cloudflare R2: {media_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete Cloudflare R2 media: {str(e)}")
            return False
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type based on file extension."""
        ext = filename.lower().split('.')[-1]
        content_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'svg': 'image/svg+xml',
            'mp4': 'video/mp4',
            'webm': 'video/webm',
            'pdf': 'application/pdf'
        }
        return content_types.get(ext, 'application/octet-stream')


class MediaStorageManager:
    """
    Media storage manager for handling multiple storage providers.
    
    Provides a unified interface for media storage operations
    across different providers with automatic failover.
    """
    
    def __init__(self, primary_provider: Optional[MediaStorageProvider] = None):
        """
        Initialize media storage manager.
        
        Args:
            primary_provider: Primary storage provider
        """
        self.primary_provider = primary_provider
        self.fallback_providers: List[MediaStorageProvider] = []
        self.logger = logging.getLogger(__name__)
    
    def add_fallback_provider(self, provider: MediaStorageProvider):
        """Add a fallback storage provider."""
        self.fallback_providers.append(provider)
    
    async def upload_media(
        self, 
        media_data: bytes, 
        filename: str,
        folder: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        use_fallback: bool = True
    ) -> Dict[str, Any]:
        """
        Upload media using primary provider with fallback support.
        
        Args:
            media_data: Media file data
            filename: Original filename
            folder: Upload folder
            metadata: Additional metadata
            use_fallback: Whether to try fallback providers on failure
            
        Returns:
            Dictionary containing upload details
        """
        if not self.primary_provider:
            raise ValueError("No primary storage provider configured")
        
        # Try primary provider first
        try:
            return await self.primary_provider.upload_media(
                media_data, filename, folder, metadata
            )
        except Exception as e:
            self.logger.warning(f"Primary storage provider failed: {str(e)}")
            
            if use_fallback:
                # Try fallback providers
                for provider in self.fallback_providers:
                    try:
                        return await provider.upload_media(
                            media_data, filename, folder, metadata
                        )
                    except Exception as fallback_error:
                        self.logger.warning(f"Fallback provider failed: {str(fallback_error)}")
                        continue
            
            # All providers failed
            raise Exception(f"All storage providers failed. Last error: {str(e)}")
    
    async def get_media_url(self, media_id: str, **kwargs) -> str:
        """
        Get media URL from primary provider.
        
        Args:
            media_id: Media identifier
            **kwargs: Provider-specific arguments
            
        Returns:
            Public URL
        """
        if not self.primary_provider:
            raise ValueError("No primary storage provider configured")
        
        return await self.primary_provider.get_media_url(media_id, **kwargs)
    
    async def delete_media(self, media_id: str) -> bool:
        """
        Delete media from primary provider.
        
        Args:
            media_id: Media identifier
            
        Returns:
            True if successful
        """
        if not self.primary_provider:
            raise ValueError("No primary storage provider configured")
        
        return await self.primary_provider.delete_media(media_id)
    
    async def batch_upload_media(
        self,
        media_files: List[Dict[str, Any]],
        folder: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Upload multiple media files.
        
        Args:
            media_files: List of media file dictionaries
            folder: Upload folder
            
        Returns:
            List of upload results
        """
        results = []
        
        for media_file in media_files:
            try:
                result = await self.upload_media(
                    media_data=media_file["data"],
                    filename=media_file["filename"],
                    folder=folder,
                    metadata=media_file.get("metadata")
                )
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to upload {media_file.get('filename', 'unknown')}: {str(e)}")
                results.append({
                    "error": str(e),
                    "filename": media_file.get("filename", "unknown")
                })
        
        return results


# Factory functions for easy setup
def create_cloudinary_storage(
    cloud_name: Optional[str] = None,
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
    folder: Optional[str] = None
) -> CloudinaryStorage:
    """Create a Cloudinary storage provider."""
    return CloudinaryStorage(cloud_name, api_key, api_secret, folder)


def create_cloudflare_r2_storage(
    account_id: Optional[str] = None,
    access_key_id: Optional[str] = None,
    secret_access_key: Optional[str] = None,
    bucket_name: Optional[str] = None,
    custom_domain: Optional[str] = None
) -> CloudflareR2Storage:
    """Create a Cloudflare R2 storage provider."""
    return CloudflareR2Storage(account_id, access_key_id, secret_access_key, bucket_name, custom_domain)


def create_media_storage_manager(
    primary_provider: Optional[MediaStorageProvider] = None
) -> MediaStorageManager:
    """Create a media storage manager with optional primary provider."""
    return MediaStorageManager(primary_provider)









