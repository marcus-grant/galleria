import re
import json
from pathlib import Path
from src.models.photo import GalleryMetadata
import settings


class PhotoMetadataService:
    def _generate_photo_url(self, relative_path: str) -> str:
        """Generate absolute or relative URL for a photo based on deployment settings.
        
        Args:
            relative_path: Relative path from metadata (e.g., 'full/photo.jpg', 'web/photo.jpg', 'photo.webp')
            
        Returns:
            Complete URL for the photo
        """
        # Determine if we're in dual bucket mode
        from src.services.s3_storage import is_dual_bucket_configured
        is_dual_mode = is_dual_bucket_configured()
        
        # Check if we have a photos base URL configured
        photos_base_url = getattr(settings, 'PHOTOS_BASE_URL', None)
        
        if photos_base_url:
            # Use configured photos base URL
            if is_dual_mode:
                # In dual bucket mode, photos are stored without 'photos/' prefix
                # Remove any 'photos/' prefix and path prefixes for thumbnails
                if relative_path.startswith('full/') or relative_path.startswith('web/'):
                    # Keep the directory structure for full/web photos
                    clean_path = relative_path
                else:
                    # For thumbnails, they're stored in the root of photos bucket
                    clean_path = relative_path
            else:
                # In single bucket mode, photos are stored with 'photos/' prefix
                if relative_path.startswith('full/') or relative_path.startswith('web/'):
                    clean_path = f"photos/{relative_path}"
                else:
                    clean_path = f"photos/thumb/{relative_path}"
            
            return f"{photos_base_url.rstrip('/')}/{clean_path}"
        else:
            # Fall back to relative URLs
            if relative_path.startswith('full/') or relative_path.startswith('web/'):
                return f"photos/{relative_path}"
            else:
                return f"photos/thumb/{relative_path}"
    
    def scan_processed_photos(self):
        prod_pics_dir = Path("prod/pics/full")
        if not prod_pics_dir.exists():
            return []
        
        photos = list(prod_pics_dir.glob("*.jpg"))
        # Sort by filename to maintain chronological order
        photos.sort(key=lambda p: p.name)
        return photos
    
    def extract_metadata_from_filename(self, filename):
        # Pattern: collection-YYYYMMDDTHHMMSS-camera-counter.jpg
        # Example: wedding-20250809T132034-r5a-0.jpg
        pattern = r"([^-]+)-(\d{8}T\d{6})-([^-]+)-([0-9A-V])\.jpg"
        match = re.match(pattern, filename)
        
        if not match:
            return {}
        
        return {
            "collection": match.group(1),
            "timestamp": match.group(2),
            "camera": match.group(3),
            "counter": match.group(4)
        }
    
    def generate_json_metadata(self):
        photos = self.scan_processed_photos()
        photo_data = []
        
        for photo_path in photos:
            filename = photo_path.name
            metadata = self.extract_metadata_from_filename(filename)
            
            if metadata:
                # Generate URLs for the photos
                base_name = filename.replace('.jpg', '')
                # Check if WebP thumbnail exists, otherwise fall back to JPEG
                webp_thumb = f"{base_name}.webp"
                thumb_path = Path("prod/pics/thumb") / webp_thumb
                if thumb_path.exists():
                    thumb_filename = webp_thumb
                else:
                    thumb_filename = filename
                    
                photo_data.append({
                    "filename": filename,
                    "timestamp": metadata["timestamp"],
                    "camera": metadata["camera"],
                    "counter": metadata["counter"],
                    "thumb_url": f"photos/{thumb_filename}",
                    "web_url": f"photos/{filename}",
                    "full_url": f"photos/{filename}"
                })
        
        return {"photos": photo_data}
    
    def generate_json_metadata_from_file(self, metadata_file_path: str) -> dict:
        """Generate frontend JSON metadata from gallery-metadata.json file.
        
        Args:
            metadata_file_path: Path to gallery-metadata.json file
            
        Returns:
            Dictionary with frontend-optimized photo data
        """
        with open(metadata_file_path, 'r') as f:
            metadata_dict = json.load(f)
        
        # Parse using dataclass
        gallery_metadata = GalleryMetadata.from_dict(metadata_dict)
        
        photo_data = []
        
        for photo in gallery_metadata.photos:
            # Combine camera make and model
            camera_parts = []
            if photo.exif.camera.get("make"):
                camera_parts.append(photo.exif.camera["make"])
            if photo.exif.camera.get("model"):
                camera_parts.append(photo.exif.camera["model"])
            camera_name = " ".join(camera_parts) if camera_parts else "Unknown"
            
            photo_data.append({
                "id": photo.id,
                "timestamp": photo.exif.corrected_timestamp,
                "camera": camera_name,
                "full_url": self._generate_photo_url(photo.files.full),
                "web_url": self._generate_photo_url(photo.files.web),
                "thumb_url": self._generate_photo_url(photo.files.thumb)
            })
        
        return {"photos": photo_data}