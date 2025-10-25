import os
import shutil
import logging
import uuid
from pathlib import Path
from typing import Optional
import requests
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class LocalStorage:
    """Handle local file storage for images"""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or os.getenv("LOCAL_STORAGE_PATH", "./storage"))
        self.images_path = self.base_path / "images"
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist"""
        self.base_path.mkdir(exist_ok=True)
        self.images_path.mkdir(exist_ok=True)
        logger.info(f"Storage directories ensured at {self.base_path}")
    
    def get_project_path(self, project_id: str) -> Path:
        """Get the directory path for a specific project"""
        project_path = self.images_path / str(project_id)
        project_path.mkdir(exist_ok=True)
        return project_path
    
    def get_image_path(self, project_id: str, image_id: str, file_extension: str = "jpg") -> Path:
        """Get the full path for an image file"""
        project_path = self.get_project_path(project_id)
        filename = f"{image_id}.{file_extension}"
        return project_path / filename
    
    def download_and_save_image(self, url: str, project_id: str, image_id: str) -> Optional[str]:
        """
        Download an image from URL and save it locally
        Returns the local file path if successful, None otherwise
        """
        try:
            # Determine file extension from URL
            parsed_url = urlparse(url)
            path = parsed_url.path
            file_extension = path.split('.')[-1] if '.' in path else 'jpg'
            
            # Get local file path
            local_path = self.get_image_path(project_id, image_id, file_extension)
            
            # Download the image
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Save to local file
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Image saved locally: {local_path}")
            return str(local_path)
            
        except Exception as e:
            logger.error(f"Failed to download and save image {image_id}: {e}")
            return None
    
    def delete_image(self, project_id: str, image_id: str) -> bool:
        """Delete an image file from local storage"""
        try:
            project_path = self.get_project_path(project_id)
            
            # Find the file with any extension
            for file_path in project_path.glob(f"{image_id}.*"):
                file_path.unlink()
                logger.info(f"Deleted image file: {file_path}")
                return True
            
            logger.warning(f"Image file not found for deletion: {image_id}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete image {image_id}: {e}")
            return False
    
    def get_image_url(self, project_id: str, image_id: str) -> Optional[str]:
        """Get the local URL for an image"""
        project_path = self.get_project_path(project_id)
        
        # Find the file with any extension
        for file_path in project_path.glob(f"{image_id}.*"):
            # Return relative path that can be served by FastAPI
            relative_path = file_path.relative_to(self.base_path)
            return f"/storage/{relative_path.as_posix()}"
        
        return None
    
    def list_project_images(self, project_id: str) -> list[str]:
        """List all image IDs in a project"""
        try:
            project_path = self.get_project_path(project_id)
            image_ids = []
            
            for file_path in project_path.glob("*.*"):
                if file_path.is_file() and file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                    image_id = file_path.stem
                    image_ids.append(image_id)
            
            return image_ids
            
        except Exception as e:
            logger.error(f"Failed to list images for project {project_id}: {e}")
            return []
    
    def cleanup_empty_directories(self):
        """Remove empty project directories"""
        try:
            for project_dir in self.images_path.iterdir():
                if project_dir.is_dir() and not any(project_dir.iterdir()):
                    project_dir.rmdir()
                    logger.info(f"Removed empty project directory: {project_dir}")
        except Exception as e:
            logger.error(f"Failed to cleanup empty directories: {e}")
    
    def get_storage_stats(self) -> dict:
        """Get storage statistics"""
        try:
            total_size = 0
            total_files = 0
            projects = 0
            
            for project_dir in self.images_path.iterdir():
                if project_dir.is_dir():
                    projects += 1
                    for file_path in project_dir.rglob("*"):
                        if file_path.is_file():
                            total_files += 1
                            total_size += file_path.stat().st_size
            
            return {
                "total_projects": projects,
                "total_images": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "base_path": str(self.base_path)
            }
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {}