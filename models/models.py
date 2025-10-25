from sqlalchemy import Column, String, ForeignKey, Boolean, DateTime, Text, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

# Use existing Project table from story schema - don't redefine it
# The Project model already exists in the story database

class Image(Base):
    """Enhanced Image model for local storage"""
    __tablename__ = "images"

    internal_id = Column(UUID(as_uuid=True), unique=True, primary_key=True, default=uuid.uuid4)
    id = Column(String(255), nullable=False, unique=True)  # Leonardo image ID or custom ID
    url = Column(String(500), nullable=True)  # Original Leonardo URL (optional)
    local_path = Column(String(500), nullable=True)  # Local file path
    local_url = Column(String(500), nullable=True)  # Local URL for serving
    
    # Relationships
    scene_id = Column(UUID(as_uuid=True), nullable=True)
    project_id = Column(UUID(as_uuid=True), nullable=False)  # References existing projects table
    
    # Prompt information
    prompt_artstyle = Column(Text, nullable=True)
    prompt_scenery = Column(Text, nullable=True)
    prompt_actor = Column(Text, nullable=True)
    full_prompt = Column(Text, nullable=True)  # Complete prompt used for generation
    
    # Metadata
    type = Column(String(50), nullable=True, default="generated")  # generated, uploaded, variation
    tags = Column(Text, nullable=True)  # Comma-separated tags
    generation_id = Column(String(255), nullable=True)  # Leonardo generation ID
    
    # Status and timestamps
    status = Column(String(50), nullable=False, default="active")  # active, deleted, archived
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # File information
    file_size = Column(String(20), nullable=True)  # File size in bytes
    file_format = Column(String(10), nullable=True)  # jpg, png, webp, etc.
    dimensions = Column(String(20), nullable=True)  # "512x512"

    # Relationships
    variants = relationship("ImageVariant", back_populates="image")

class ImageVariant(Base):
    """Image variants (renamed from Variants for clarity)"""
    __tablename__ = "image_variants"

    id = Column(String(255), primary_key=True)
    image_id = Column(UUID(as_uuid=True), ForeignKey("images.internal_id"), nullable=False)
    is_primary = Column(Boolean, nullable=False, default=True)
    variant_type = Column(String(50), nullable=False, default="main")  # main, upscale, variation
    created_at = Column(DateTime, default=datetime.utcnow)
    
    image = relationship("Image", back_populates="variants")

class GenerationJob(Base):
    """Track generation jobs across all providers"""
    __tablename__ = "generation_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    generation_id = Column(String(255), nullable=False, unique=True)  # Provider generation ID
    provider = Column(String(50), nullable=False)  # leonardo, runware, gemini, comfyui
    project_id = Column(UUID(as_uuid=True), nullable=False)  # References existing projects table
    
    # Generation parameters
    prompt = Column(Text, nullable=False)
    height = Column(String(10), nullable=True)
    width = Column(String(10), nullable=True)
    model_id = Column(String(255), nullable=True)
    preset_style = Column(String(50), nullable=True)
    num_images = Column(String(5), nullable=True)
    
    # Status tracking
    status = Column(String(50), nullable=False, default="pending")  # pending, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)