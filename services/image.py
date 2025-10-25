from sqlalchemy.orm import Session
from models.models import Image, ImageVariant, Project
from fastapi import HTTPException
from uuid import UUID
from services.leo_common import delete_generation_api
from utils.storage import LocalStorage
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
storage = LocalStorage()

def delete_image(db: Session, image_id: str):
    image = get_image_by_id(db, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    db.delete(image)
    db.commit()
    return image

def get_image_by_id(db: Session, image_id: str):
    return db.query(Image).filter(
        Image.id == image_id,
        Image.status == "active"
    ).first()

def get_images_by_scene_id(db: Session, scene_id: str):
    return db.query(Image).filter(Image.scene_id == scene_id).all()


def save_image(
        db: Session, 
        id: UUID, 
        url: str, 
        project_id: UUID, 
        prompt_artstyle: str = None, 
        prompt_scenery: str = None,
        prompt_actor: str = None,
        generation_id: str = None,
        type: str = "generated",
        local_path: str = None,
        full_prompt: str = None):
    """Save image with enhanced local storage support"""
    try:
        # Download and save image locally if URL is provided
        local_url = None
        if url and not local_path:
            local_path = storage.download_and_save_image(url, str(project_id), str(id))
            if local_path:
                local_url = storage.get_image_url(str(project_id), str(id))
        elif local_path:
            local_url = storage.get_image_url(str(project_id), str(id))
        
        # Create the image record
        image = Image(
            id=str(id),
            project_id=project_id,
            prompt_artstyle=prompt_artstyle,
            prompt_scenery=prompt_scenery,
            prompt_actor=prompt_actor,
            full_prompt=full_prompt,
            url=url,
            local_path=local_path,
            local_url=local_url,
            generation_id=generation_id,
            type=type,
            status="active"
        )
        db.add(image)
        db.commit()
        db.refresh(image)
        
        # Create primary variant
        variant = ImageVariant(
            id=str(id),
            is_primary=True,
            image_id=image.internal_id, 
            variant_type="main"
        )
        db.add(variant)
        db.commit()
        db.refresh(variant)
        
        logger.info(f"Image {id} saved successfully with local storage")
        return image
        
    except Exception as e:
        logger.error(f"Error saving image {id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")

def cleanup_orphaned_images(db: Session):
    """Clean up images that failed to generate or are no longer needed"""
    try:
        # Find images marked as deleted
        deleted_images = db.query(Image).filter(Image.status == "deleted").all()
        
        for image in deleted_images:
            try:
                # Delete from Leonardo if generation_id exists
                if image.generation_id:
                    delete_generation_api(image.generation_id)
                
                # Delete local file
                if image.project_id:
                    storage.delete_image(str(image.project_id), image.id)
                
                # Remove from database
                db.delete(image)
                logger.info(f"Cleaned up orphaned image: {image.id}")
                
            except Exception as e:
                logger.error(f"Error cleaning up image {image.id}: {e}")
        
        db.commit()
        storage.cleanup_empty_directories()
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        db.rollback()


def get_image_tags(image):
    """Convert image tags from string to list format"""
    if not image.tags:
        return []
        
    if ',' in image.tags:
        return [tag.strip() for tag in image.tags.split(',')]
    return [image.tags.strip()]

def create_project(db: Session, name: str, description: str = None):
    """Create a new project"""
    try:
        project = Project(
            name=name,
            description=description
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        
        # Create project directory in storage
        storage.get_project_path(str(project.id))
        
        logger.info(f"Created project: {name} ({project.id})")
        return project
        
    except Exception as e:
        logger.error(f"Error creating project {name}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")

def get_project_by_id(db: Session, project_id: UUID):
    """Get project by ID"""
    return db.query(Project).filter(Project.id == project_id).first()

def list_projects(db: Session, limit: int = 100):
    """List all projects"""
    return db.query(Project).limit(limit).all()

