from pydantic import BaseModel

class GenerateAndSaveRequest(BaseModel):
    prompt: str
    project_id: str
    prompt_artstyle: str = None
    prompt_scenery: str = None
    prompt_actor: str = None
    type: str = "gen"
    image_id: str = None
    height: int = 512
    width: int = 512
    num_images: int = 4
    preset_style: str = "DYNAMIC"
    

class GenerationRequest(BaseModel):
    prompt: str
    height: int = 512
    width: int = 512
    num_images: int = 4
    preset_style: str = "DYNAMIC"
    
class GenVideoRequest(BaseModel):
    imageId: str
    imageType: str = "GENERATED"
    prompt: str = "The scene gradually comes to life with subtle movement, light shifts, and ambient motion."
    promptEnhance: bool = True
    
