from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from services.image import get_image_by_id, get_images_by_scene_id, save_image
from schemas.image import ImageSchema, ImageSceneAssignSchema, ImageResponse, ImageTagSchema, ImageTagsUpdateResponse
from models.models import Image
from database import get_db
from uuid import UUID
import logging
router = APIRouter(tags=["Images"])

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
    logging.info(f"Getting images for project {project_id}")
    images = db.query(Image).filter(Image.project_id == project_id).all()
    logging.info(f"Found {len(images)} images")
    
    # Convert tags to lists for all images
    for image in images:
        if image.tags:
            if ',' in image.tags:
                image.tags = [tag.strip() for tag in image.tags.split(',')]
            else:
                image.tags = [image.tags.strip()]
        else:
            image.tags = []
    
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
    db.delete(image)
    db.commit()
    return image

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
