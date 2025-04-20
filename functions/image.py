from sqlalchemy.orm import Session
from models.models import Image, Variants
from fastapi import HTTPException
from uuid import UUID
from functions.leonardo import delete_generation_api

def delete_image(db: Session, image_id: str):
    image = get_image_by_id(db, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    db.delete(image)
    db.commit()
    return image

def get_image_by_id(db: Session, image_id: str):
    return db.query(Image).filter(Image.id == image_id).first()

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
        type: str = "gen"):
    image = Image(
        id=id,
        project_id=project_id,
        prompt_artstyle=prompt_artstyle,
        prompt_scenery=prompt_scenery,
        prompt_actor=prompt_actor,
        url=url,
        saved=True,
        generation_id=generation_id,
        type=type
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    
    variant = Variants(
        id=id,  
        is_primary=True,
        image_id=image.internal_id, 
        type="main"
    )
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return image

def delete_unsaved_images(db: Session):
    images = db.query(Image).filter(Image.saved == False).all()
    for image in images:
        if image.generation_id:
            try:
                delete_generation_api(image.generation_id)
                db.delete(image)
            except Exception as e:
                print(f"Error deleting generation {image.generation_id}: {e}")
    db.commit()


def get_image_tags(image):
    """Convert image tags from string to list format"""
    if not image.tags:
        return []
        
    if ',' in image.tags:
        return [tag.strip() for tag in image.tags.split(',')]
    return [image.tags.strip()]

