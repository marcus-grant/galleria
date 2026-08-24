import re
import json
from pathlib import Path
from galleria.models.photo import GalleryMetadata
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
        from galleria.services.s3_storage import is_dual_bucket_configured
        is_dual_mode = is_dual_bucket_configured()
        
        # Check if we have a pics base URL configured
        pics_base_url = getattr(settings, 'PICS_BASE_URL', None)
        
        if pics_base_url:
            # Use configured pics base URL
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
            
            return f"{pics_base_url.rstrip('/')}/{clean_path}"
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
        pics = self.scan_processed_photos()
        pic_data = []
        
        for pic_path in pics:
            filename = pic_path.name
            metadata = self.extract_metadata_from_filename(filename)
            
            if metadata:
                pic_data.append({
                    "filename": filename,
                    "timestamp": metadata["timestamp"],
                    "camera": metadata["camera"],
                    "counter": metadata["counter"]
                })
        
        return {"pics": pic_data}
    
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
        
        pic_data = []
        
        for pic in gallery_metadata.photos:
            # Combine camera make and model
            camera_parts = []
            if pic.exif.camera.get("make"):
                camera_parts.append(pic.exif.camera["make"])
            if pic.exif.camera.get("model"):
                camera_parts.append(pic.exif.camera["model"])
            camera_name = " ".join(camera_parts) if camera_parts else "Unknown"
            
            # Extract filename from any of the file paths (they all have same base name)
            filename = Path(pic.files.full).name
            
            pic_data.append({
                "id": pic.id,
                "timestamp": pic.exif.corrected_timestamp,
                "camera": camera_name,
                "filename": filename
            })
        
        return {"pics": pic_data}