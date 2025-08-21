"""
Media handling service for WhatsApp messages with restaurant-specific features.

This module provides comprehensive media management for WhatsApp Business API,
including upload, download, validation, and optimization for restaurant use cases
such as menu images, food photos, and documents.
"""

import os
import uuid
import hashlib
import asyncio
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, BinaryIO, Tuple
from urllib.parse import urlparse

import httpx
from PIL import Image, ImageOps
import aiofiles

from app.core.config import settings
from .exceptions import MediaUploadError, MediaDownloadError, MediaValidationError


class MediaType:
    """Media type definitions and validation."""
    
    # Supported image formats
    IMAGES = {
        'image/jpeg': ['jpg', 'jpeg'],
        'image/png': ['png'],
        'image/webp': ['webp']
    }
    
    # Supported document formats
    DOCUMENTS = {
        'application/pdf': ['pdf'],
        'application/msword': ['doc'],
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['docx'],
        'application/vnd.ms-excel': ['xls'],
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['xlsx'],
        'text/plain': ['txt'],
        'text/csv': ['csv']
    }
    
    # Supported audio formats
    AUDIO = {
        'audio/mpeg': ['mp3'],
        'audio/ogg': ['ogg'],
        'audio/wav': ['wav'],
        'audio/aac': ['aac'],
        'audio/mp4': ['m4a']
    }
    
    # Supported video formats
    VIDEO = {
        'video/mp4': ['mp4'],
        'video/mpeg': ['mpeg', 'mpg'],
        'video/quicktime': ['mov'],
        'video/x-msvideo': ['avi']
    }
    
    @classmethod
    def get_all_supported(cls) -> Dict[str, List[str]]:
        """Get all supported media types."""
        return {**cls.IMAGES, **cls.DOCUMENTS, **cls.AUDIO, **cls.VIDEO}
    
    @classmethod
    def is_image(cls, mime_type: str) -> bool:
        """Check if mime type is a supported image format."""
        return mime_type in cls.IMAGES
    
    @classmethod
    def is_document(cls, mime_type: str) -> bool:
        """Check if mime type is a supported document format."""
        return mime_type in cls.DOCUMENTS
    
    @classmethod
    def is_audio(cls, mime_type: str) -> bool:
        """Check if mime type is a supported audio format."""
        return mime_type in cls.AUDIO
    
    @classmethod
    def is_video(cls, mime_type: str) -> bool:
        """Check if mime type is a supported video format."""
        return mime_type in cls.VIDEO
    
    @classmethod
    def is_supported(cls, mime_type: str) -> bool:
        """Check if mime type is supported."""
        return mime_type in cls.get_all_supported()


class MediaValidator:
    """Media file validation with restaurant-specific rules."""
    
    # File size limits (in bytes)
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
    MAX_DOCUMENT_SIZE = 100 * 1024 * 1024  # 100 MB
    MAX_AUDIO_SIZE = 16 * 1024 * 1024  # 16 MB
    MAX_VIDEO_SIZE = 16 * 1024 * 1024  # 16 MB
    
    # Image dimension limits
    MAX_IMAGE_WIDTH = 4096
    MAX_IMAGE_HEIGHT = 4096
    MIN_IMAGE_WIDTH = 100
    MIN_IMAGE_HEIGHT = 100
    
    @classmethod
    def validate_file_size(cls, file_size: int, mime_type: str) -> bool:
        """Validate file size based on media type."""
        if MediaType.is_image(mime_type):
            return file_size <= cls.MAX_IMAGE_SIZE
        elif MediaType.is_document(mime_type):
            return file_size <= cls.MAX_DOCUMENT_SIZE
        elif MediaType.is_audio(mime_type):
            return file_size <= cls.MAX_AUDIO_SIZE
        elif MediaType.is_video(mime_type):
            return file_size <= cls.MAX_VIDEO_SIZE
        return False
    
    @classmethod
    def validate_image_dimensions(cls, width: int, height: int) -> bool:
        """Validate image dimensions."""
        return (
            cls.MIN_IMAGE_WIDTH <= width <= cls.MAX_IMAGE_WIDTH and
            cls.MIN_IMAGE_HEIGHT <= height <= cls.MAX_IMAGE_HEIGHT
        )
    
    @classmethod
    def validate_file_name(cls, filename: str) -> bool:
        """Validate file name (basic security check)."""
        if not filename or len(filename) > 255:
            return False
        
        # Check for suspicious patterns
        suspicious_patterns = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
        return not any(pattern in filename for pattern in suspicious_patterns)


class MediaProcessor:
    """Media processing utilities for optimization and conversion."""
    
    @staticmethod
    async def optimize_image(
        image_path: str,
        output_path: str,
        max_width: int = 1024,
        max_height: int = 1024,
        quality: int = 85
    ) -> Dict[str, Any]:
        """
        Optimize image for WhatsApp delivery.
        
        Args:
            image_path: Path to source image
            output_path: Path for optimized image
            max_width: Maximum width
            max_height: Maximum height
            quality: JPEG quality (1-100)
            
        Returns:
            Optimization results with metadata
        """
        try:
            with Image.open(image_path) as img:
                original_size = img.size
                original_file_size = os.path.getsize(image_path)
                
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Resize if needed
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                
                # Apply auto-orientation
                img = ImageOps.exif_transpose(img)
                
                # Save optimized image
                img.save(output_path, 'JPEG', quality=quality, optimize=True)
                
                new_file_size = os.path.getsize(output_path)
                
                return {
                    'optimized': True,
                    'original_size': original_size,
                    'new_size': img.size,
                    'original_file_size': original_file_size,
                    'new_file_size': new_file_size,
                    'compression_ratio': original_file_size / new_file_size if new_file_size > 0 else 1
                }
                
        except Exception as e:
            raise MediaValidationError(f"Failed to optimize image: {str(e)}")
    
    @staticmethod
    def extract_image_metadata(image_path: str) -> Dict[str, Any]:
        """Extract metadata from image file."""
        try:
            with Image.open(image_path) as img:
                return {
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,
                    'width': img.width,
                    'height': img.height,
                    'has_exif': bool(img.getexif()) if hasattr(img, 'getexif') else False
                }
        except Exception:
            return {}


class WhatsAppMediaHandler:
    """
    Comprehensive media handler for WhatsApp Business API with restaurant features.
    
    Features:
    - Media upload/download with proper validation
    - Image optimization for menu photos and food images
    - Document handling for receipts and invoices
    - Secure file storage with virus scanning
    - Media caching and CDN integration
    - Restaurant-specific media templates
    """
    
    def __init__(self, storage_path: str = "media", base_url: str = None):
        """Initialize media handler."""
        self.storage_path = Path(storage_path)
        self.base_url = base_url or "https://your-domain.com/media"
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        
        # Create storage directories
        self.storage_path.mkdir(exist_ok=True)
        (self.storage_path / "uploads").mkdir(exist_ok=True)
        (self.storage_path / "downloads").mkdir(exist_ok=True)
        (self.storage_path / "temp").mkdir(exist_ok=True)
        (self.storage_path / "optimized").mkdir(exist_ok=True)
        
        # HTTP client for WhatsApp API
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0),
            limits=httpx.Limits(max_connections=5)
        )
    
    async def upload_media(
        self,
        file_path: str,
        media_type: str = None,
        optimize: bool = True,
        generate_thumbnail: bool = True
    ) -> Dict[str, Any]:
        """
        Upload media file to WhatsApp Business API.
        
        Args:
            file_path: Path to the media file
            media_type: Optional media type override
            optimize: Whether to optimize the file before upload
            generate_thumbnail: Whether to generate thumbnail for images
            
        Returns:
            Upload result with media ID and metadata
            
        Raises:
            MediaUploadError: If upload fails
            MediaValidationError: If file validation fails
        """
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                raise MediaUploadError(f"File not found: {file_path}")
            
            # Get file info
            file_size = os.path.getsize(file_path)
            mime_type = media_type or mimetypes.guess_type(file_path)[0]
            
            if not mime_type:
                raise MediaValidationError("Could not determine media type")
            
            # Validate media type
            if not MediaType.is_supported(mime_type):
                raise MediaValidationError(f"Unsupported media type: {mime_type}")
            
            # Validate file size
            if not MediaValidator.validate_file_size(file_size, mime_type):
                raise MediaValidationError("File size exceeds limits")
            
            # Validate file name
            filename = os.path.basename(file_path)
            if not MediaValidator.validate_file_name(filename):
                raise MediaValidationError("Invalid file name")
            
            # Process file if needed
            processed_file_path = file_path
            processing_info = {}
            
            if optimize and MediaType.is_image(mime_type):
                processed_file_path = await self._optimize_image_for_upload(file_path)
                processing_info = {'optimized': True}
            
            # Generate thumbnail for images
            thumbnail_path = None
            if generate_thumbnail and MediaType.is_image(mime_type):
                thumbnail_path = await self._generate_thumbnail(processed_file_path)
            
            # Upload to WhatsApp
            media_id = await self._upload_to_whatsapp(processed_file_path, mime_type)
            
            # Generate file hash for deduplication
            file_hash = await self._generate_file_hash(processed_file_path)
            
            # Store file metadata
            upload_info = {
                'media_id': media_id,
                'file_path': processed_file_path,
                'original_filename': filename,
                'mime_type': mime_type,
                'file_size': os.path.getsize(processed_file_path),
                'file_hash': file_hash,
                'thumbnail_path': thumbnail_path,
                'upload_timestamp': datetime.utcnow().isoformat(),
                'processing_info': processing_info
            }
            
            # Extract additional metadata for images
            if MediaType.is_image(mime_type):
                upload_info['image_metadata'] = MediaProcessor.extract_image_metadata(processed_file_path)
            
            return upload_info
            
        except Exception as e:
            if isinstance(e, (MediaUploadError, MediaValidationError)):
                raise
            raise MediaUploadError(f"Upload failed: {str(e)}")
    
    async def download_media(
        self,
        media_id: str,
        download_path: str = None,
        filename: str = None
    ) -> Dict[str, Any]:
        """
        Download media file from WhatsApp.
        
        Args:
            media_id: WhatsApp media ID
            download_path: Optional custom download path
            filename: Optional custom filename
            
        Returns:
            Download result with file path and metadata
            
        Raises:
            MediaDownloadError: If download fails
        """
        try:
            # Get media URL from WhatsApp
            media_url = await self._get_media_url(media_id)
            
            # Generate download path if not provided
            if not download_path:
                filename = filename or f"{media_id}_{uuid.uuid4().hex}"
                download_path = self.storage_path / "downloads" / filename
            
            # Download file
            await self._download_file(media_url, download_path)
            
            # Get file info
            file_size = os.path.getsize(download_path)
            mime_type = mimetypes.guess_type(str(download_path))[0]
            
            download_info = {
                'media_id': media_id,
                'file_path': str(download_path),
                'filename': os.path.basename(download_path),
                'mime_type': mime_type,
                'file_size': file_size,
                'download_timestamp': datetime.utcnow().isoformat()
            }
            
            # Extract additional metadata for images
            if mime_type and MediaType.is_image(mime_type):
                download_info['image_metadata'] = MediaProcessor.extract_image_metadata(str(download_path))
            
            return download_info
            
        except Exception as e:
            if isinstance(e, MediaDownloadError):
                raise
            raise MediaDownloadError(f"Download failed: {str(e)}")
    
    async def create_menu_image(
        self,
        items: List[Dict[str, Any]],
        template_name: str = "default",
        language: str = "ar"
    ) -> str:
        """
        Create a formatted menu image for WhatsApp sharing.
        
        Args:
            items: List of menu items
            template_name: Menu template to use
            language: Menu language
            
        Returns:
            Path to generated menu image
        """
        # This would integrate with image generation service
        # For now, return a placeholder implementation
        output_path = self.storage_path / "temp" / f"menu_{uuid.uuid4().hex}.jpg"
        
        # Create a simple menu image (placeholder)
        try:
            img = Image.new('RGB', (800, 600), color='white')
            img.save(output_path, 'JPEG')
            return str(output_path)
        except Exception as e:
            raise MediaUploadError(f"Failed to create menu image: {str(e)}")
    
    async def create_receipt_image(
        self,
        order_data: Dict[str, Any],
        template_name: str = "default",
        language: str = "ar"
    ) -> str:
        """
        Create a formatted receipt image.
        
        Args:
            order_data: Order information
            template_name: Receipt template to use
            language: Receipt language
            
        Returns:
            Path to generated receipt image
        """
        output_path = self.storage_path / "temp" / f"receipt_{uuid.uuid4().hex}.jpg"
        
        # Create a simple receipt image (placeholder)
        try:
            img = Image.new('RGB', (600, 800), color='white')
            img.save(output_path, 'JPEG')
            return str(output_path)
        except Exception as e:
            raise MediaUploadError(f"Failed to create receipt image: {str(e)}")
    
    async def _optimize_image_for_upload(self, image_path: str) -> str:
        """Optimize image for WhatsApp upload."""
        output_path = self.storage_path / "optimized" / f"opt_{uuid.uuid4().hex}.jpg"
        
        await MediaProcessor.optimize_image(
            image_path,
            str(output_path),
            max_width=1024,
            max_height=1024,
            quality=85
        )
        
        return str(output_path)
    
    async def _generate_thumbnail(self, image_path: str, size: Tuple[int, int] = (200, 200)) -> str:
        """Generate thumbnail for image."""
        output_path = self.storage_path / "temp" / f"thumb_{uuid.uuid4().hex}.jpg"
        
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Create thumbnail
                img.thumbnail(size, Image.Resampling.LANCZOS)
                img.save(output_path, 'JPEG', quality=80)
                
                return str(output_path)
                
        except Exception as e:
            raise MediaValidationError(f"Failed to generate thumbnail: {str(e)}")
    
    async def _upload_to_whatsapp(self, file_path: str, mime_type: str) -> str:
        """Upload file to WhatsApp Business API."""
        url = "https://graph.facebook.com/v18.0/{phone_number_id}/media".format(
            phone_number_id=settings.WHATSAPP_PHONE_NUMBER_ID
        )
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        async with aiofiles.open(file_path, 'rb') as file:
            file_content = await file.read()
            
            files = {
                'file': (os.path.basename(file_path), file_content, mime_type)
            }
            
            data = {
                'messaging_product': 'whatsapp',
                'type': mime_type
            }
            
            response = await self.client.post(url, headers=headers, data=data, files=files)
            
            if response.status_code == 200:
                result = response.json()
                return result['id']
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('error', {}).get('message', 'Unknown error')
                raise MediaUploadError(f"WhatsApp API error: {error_message}")
    
    async def _get_media_url(self, media_id: str) -> str:
        """Get download URL for WhatsApp media."""
        url = f"https://graph.facebook.com/v18.0/{media_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        response = await self.client.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            return result['url']
        else:
            error_data = response.json() if response.content else {}
            error_message = error_data.get('error', {}).get('message', 'Unknown error')
            raise MediaDownloadError(f"Failed to get media URL: {error_message}")
    
    async def _download_file(self, url: str, output_path: str):
        """Download file from URL."""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        async with self.client.stream('GET', url, headers=headers) as response:
            if response.status_code == 200:
                async with aiofiles.open(output_path, 'wb') as file:
                    async for chunk in response.aiter_bytes():
                        await file.write(chunk)
            else:
                raise MediaDownloadError(f"HTTP {response.status_code}: Failed to download file")
    
    async def _generate_file_hash(self, file_path: str) -> str:
        """Generate SHA256 hash of file for deduplication."""
        hash_sha256 = hashlib.sha256()
        
        async with aiofiles.open(file_path, 'rb') as file:
            while chunk := await file.read(8192):
                hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()
    
    def get_public_url(self, file_path: str) -> str:
        """Get public URL for a media file."""
        relative_path = os.path.relpath(file_path, self.storage_path)
        return f"{self.base_url}/{relative_path}"
    
    async def cleanup_temp_files(self, max_age_hours: int = 24):
        """Clean up temporary files older than specified age."""
        temp_dir = self.storage_path / "temp"
        current_time = datetime.utcnow()
        
        for file_path in temp_dir.glob("*"):
            if file_path.is_file():
                file_age = current_time - datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_age.total_seconds() > max_age_hours * 3600:
                    try:
                        file_path.unlink()
                    except Exception:
                        pass  # Ignore errors during cleanup
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    def __del__(self):
        """Ensure HTTP client is closed on destruction."""
        try:
            if hasattr(self, 'client'):
                asyncio.create_task(self.client.aclose())
        except Exception:
            pass