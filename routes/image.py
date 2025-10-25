from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from services.image import get_image_by_id, get_images_by_scene_id, save_image
from schemas.image import ImageSchema, ImageSceneAssignSchema, ImageResponse, ImageTagSchema, ImageTagsUpdateResponse
from models.models import Image, Project
from database import get_db
from utils.storage import LocalStorage
from uuid import UUID
import logging
import os
from pathlib import Path

router = APIRouter(tags=["Images"])
storage = LocalStorage()
logger = logging.getLogger(__name__)

@router.post("/")
def save_image_endpoint(image: ImageSchema, db: Session = Depends(get_db)):
    try:
        return save_image(db, 
                          image.id, 
                          image.url, 
                          project_id=image.project_id, 
                          prompt_artstyle=image.prompt_artstyle,
                          prompt_scenery=image.prompt_scenery, 
                          prompt_actor=image.prompt_actor, 
                          type=image.type)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Assign scene to the image
@router.post("/assign", response_model=ImageResponse)
def assign_scene_to_image_endpoint(payload: ImageSceneAssignSchema, db: Session = Depends(get_db)):
    # Convert UUID to string if necessary
    image_id_str = str(payload.image_id)
    scene_id_str = str(payload.scene_id) if payload.scene_id else None
    image = db.query(Image).filter(Image.id == image_id_str).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    if scene_id_str is None:
        raise HTTPException(status_code=400, detail="scene_id cannot be null")
    existing_image = db.query(Image).filter(
        Image.scene_id == scene_id_str).first()
    if existing_image and existing_image.id != image_id_str:
        existing_image.scene_id = None
    image.scene_id = scene_id_str
    # TBD error handling if no scene
    db.commit()
    db.refresh(image)

    return image


# Get images by project
@router.get("/project/{project_id}")
def get_images_by_project_id_endpoint(project_id: UUID, db: Session = Depends(get_db)):
    logger.info(f"Getting images for project {project_id}")
    images = db.query(Image).filter(
        Image.project_id == project_id,
        Image.status == "active"
    ).all()
    logger.info(f"Found {len(images)} images")
    
    # Convert tags to lists and ensure local URLs are available
    for image in images:
        # Handle tags
        if image.tags:
            if ',' in image.tags:
                image.tags = [tag.strip() for tag in image.tags.split(',')]
            else:
                image.tags = [image.tags.strip()]
        else:
            image.tags = []
        
        # Ensure local_url is set for serving images
        if not image.local_url and image.local_path:
            image.local_url = storage.get_image_url(str(project_id), image.id)
    
    return images if images else []


@router.get("/id/{image_id}")
def get_image_by_id_endpoint(image_id: str, db: Session = Depends(get_db)):
    image = get_image_by_id(db, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
        
    # Convert tags to a list before returning
    if image.tags:
        if ',' in image.tags:
            image.tags = [tag.strip() for tag in image.tags.split(',')]
        else:
            image.tags = [image.tags.strip()]
    else:
        image.tags = []
        
    return image


@router.get("/scene/{scene_id}")
def get_images_by_scene_id_endpoint(scene_id: str, db: Session = Depends(get_db)):
    images = get_images_by_scene_id(db, scene_id)
    return images if images else []


@router.delete("/{image_id}")
def delete_image_endpoint(image_id: str, db: Session = Depends(get_db)):
    image = get_image_by_id(db, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Delete local file
    if image.project_id:
        storage.delete_image(str(image.project_id), image_id)
    
    # Mark as deleted instead of hard delete (for data integrity)
    image.status = "deleted"
    db.commit()
    db.refresh(image)
    
    return {"message": "Image deleted successfully", "id": image_id}

@router.post("/tag", response_model=ImageTagsUpdateResponse)
def add_tag_to_image_endpoint(payload: ImageTagSchema, db: Session = Depends(get_db)):
    """Add a tag to an image"""
    image = db.query(Image).filter(Image.id == str(payload.image_id)).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Handle both string and list formats for tags
    current_tags = []
    if image.tags:
        if ',' in image.tags:  # Handle comma-separated string
            current_tags = [tag.strip() for tag in image.tags.split(',')]
        else:  # Handle single string
            current_tags = [image.tags.strip()]
    
    # Only add the tag if it doesn't already exist
    if payload.tag not in current_tags:
        current_tags.append(payload.tag)
        image.tags = ','.join(current_tags)
        db.commit()
        
    return {
        "id": image.id,
        "tags": current_tags
    }

@router.delete("/tag", response_model=ImageTagsUpdateResponse)
def remove_tag_from_image_endpoint(payload: ImageTagSchema, db: Session = Depends(get_db)):
    """Remove a tag from an image"""
    image = db.query(Image).filter(Image.id == str(payload.image_id)).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Skip if no tags exist
    if not image.tags:
        return {
            "id": image.id,
            "tags": []
        }
    
    # Handle both string and list formats
    current_tags = []
    if ',' in image.tags:
        current_tags = [tag.strip() for tag in image.tags.split(',')]
    else:
        current_tags = [image.tags.strip()]
    
    # Remove the tag if it exists
    if payload.tag in current_tags:
        current_tags.remove(payload.tag)
        image.tags = ','.join(current_tags) if current_tags else None
        db.commit()
    
    return {
        "id": image.id,
        "tags": current_tags
    }

@router.get("/{image_id}/tags", response_model=ImageTagsUpdateResponse)
def get_image_tags_endpoint(image_id: str, db: Session = Depends(get_db)):
    """Get all tags for an image"""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Convert tags string to list
    tags = []
    if image.tags:
        if ',' in image.tags:
            tags = [tag.strip() for tag in image.tags.split(',')]
        else:
            tags = [image.tags.strip()]
    
    return {
        "id": image.id,
        "tags": tags
    }

# New routes for local file serving and project management

@router.get("/storage/{project_id}/{filename}")
def serve_local_image(project_id: str, filename: str):
    """Serve local image files"""
    try:
        file_path = storage.get_project_path(project_id) / filename
        
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="Image file not found")
        
        return FileResponse(
            path=file_path,
            media_type="image/*",
            filename=filename
        )
    except Exception as e:
        logger.error(f"Error serving image {filename}: {e}")
        raise HTTPException(status_code=500, detail="Error serving image")

@router.get("/projects/{project_id}/stats")
def get_project_stats(project_id: UUID, db: Session = Depends(get_db)):
    """Get statistics for a project"""
    try:
        # Database stats
        total_images = db.query(Image).filter(
            Image.project_id == project_id,
            Image.status == "active"
        ).count()
        
        # Local storage stats
        local_images = storage.list_project_images(str(project_id))
        
        return {
            "project_id": str(project_id),
            "total_images_db": total_images,
            "total_images_local": len(local_images),
            "local_storage_path": str(storage.get_project_path(str(project_id)))
        }
    except Exception as e:
        logger.error(f"Error getting project stats: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving project stats")

@router.get("/storage/stats")
def get_storage_stats():
    """Get overall storage statistics"""
    try:
        stats = storage.get_storage_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting storage stats: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving storage stats")

@router.post("/storage/cleanup")
def cleanup_storage():
    """Clean up empty directories and orphaned files"""
    try:
        storage.cleanup_empty_directories()
        return {"message": "Storage cleanup completed"}
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise HTTPException(status_code=500, detail="Error during storage cleanup")
