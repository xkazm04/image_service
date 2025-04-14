from pydantic import BaseModel

class GenerationSchema(BaseModel):
    id: str
    project_id: str
    assigned_scene: str = None
    prompt: str = None