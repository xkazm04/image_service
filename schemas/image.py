from pydantic import BaseModel
from typing import Optional, List, Union
from uuid import UUID

class ImageSceneAssignSchema(BaseModel):
    image_id: UUID
    scene_id: Optional[UUID]  
    prompt: Optional[str]

class ImageResponse(BaseModel):
    internal_id: UUID
    id: str
    url: str
    scene_id: Optional[UUID] = None
    prompt_artstyle: Optional[str] = None
    prompt_scenery: Optional[str] = None
    prompt_actor: Optional[str] = None
    project_id: UUID
    type: Optional[str] = None
    tags: Optional[Union[str, List[str]]] = None

    class Config:
        orm_mode = True
        
class ImageSchema(BaseModel):
    id: UUID
    url: str
    project_id: UUID
    prompt_artstyle: Optional[str] = None
    prompt_scenery: Optional[str] = None
    prompt_actor: Optional[str] = None
    type: Optional[str] = "gen"
    tags: Optional[Union[str, List[str]]] = None

    class Config:
        orm_mode = True

class ImageTagSchema(BaseModel):
    image_id: UUID
    tag: str

class ImageTagsUpdateResponse(BaseModel):
    id: str
    tags: Optional[List[str]] = None
    
    class Config:
        orm_mode = True