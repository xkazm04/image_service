from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()


class Generation(Base):
    __tablename__ = "generations"

    id = Column(String, primary_key=True)
    project_id = Column(UUID(as_uuid=True), nullable=False)
    assigned_scene = Column(UUID(as_uuid=True), nullable=True)
    
     
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
    type = Column(String, nullable=True)
    tags = Column(String, nullable=True)

