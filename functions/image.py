from sqlalchemy.orm import Session
from models.models import Image
from fastapi import HTTPException
from uuid import UUID

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
        type: str = "gen"):
    image = Image(
        id=id,
        project_id=project_id,
        prompt_artstyle=prompt_artstyle,
        prompt_scenery=prompt_scenery,
        prompt_actor=prompt_actor,
        url=url,
        type=type
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image

def get_image_tags(image):
    """Convert image tags from string to list format"""
    if not image.tags:
        return []
        
    if ',' in image.tags:
        return [tag.strip() for tag in image.tags.split(',')]
    return [image.tags.strip()]

