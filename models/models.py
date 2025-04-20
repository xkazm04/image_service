from sqlalchemy import Column, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()
     
class Image(Base):
    __tablename__ = "images"

    internal_id = Column(UUID(as_uuid=True), unique=True, primary_key=True, default=uuid.uuid4)
    id = Column(String, nullable=False)
    url = Column(String, nullable=False)
    scene_id = Column(UUID(as_uuid=True), nullable=True)
    prompt_artstyle = Column(String, nullable=True)
    prompt_scenery = Column(String, nullable=True)
    prompt_actor = Column(String, nullable=True)
    project_id = Column(UUID(as_uuid=True), nullable=False)
    saved = Column(Boolean, nullable=True, default=False)
    type = Column(String, nullable=True)
    tags = Column(String, nullable=True)
    generation_id = Column(String, nullable=True)

    variants = relationship("Variants", back_populates="image")

class Variants(Base):
    __tablename__ = "variants"

    id = Column(String, primary_key=True)
    image_id = Column(UUID(as_uuid=True), ForeignKey("images.internal_id"), nullable=False)
    is_primary = Column(Boolean, nullable=False) 
    type = Column(String, nullable=False)
    predecessor_id = Column(String, nullable=True)
    
    image = relationship("Image", back_populates="variants")