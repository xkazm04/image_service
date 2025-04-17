import logging
from fastapi import APIRouter, HTTPException, Query, Depends
from functions.leonardo import create_generation, get_generation, improve_prompt_api
import asyncio
from pydantic import BaseModel
from celery_config import monitor_background_removal
from functions.image import save_image
from sqlalchemy.orm import Session
router = APIRouter(tags=["Leo"])
from database import get_db
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
    
# Dummy get to validate routing
@router.get("/")
async def root():
    return {"message": "Welcome to the Leonardo API"}
    
@router.post("/generate")
async def generate_and_poll_images(request: GenerationRequest):
    try:
        # Trigger image generation
        create_response = create_generation(
            prompt=request.prompt,
            height=request.height,
            width=request.width,
            num_images=request.num_images,
            preset_style=request.preset_style,
        )
        generation_id = create_response["sdGenerationJob"]["generationId"]

        # Poll for generated images
        for attempt in range(10):  # Poll for up to 10 attempts
            try:
                images = get_generation(generation_id)
                if images:  # If images are available, return them immediately
                    logging.info(f"Images found after {attempt + 1} attempts.")
                    return {"status": "success", "data": images}
            except Exception as e:
                # Log polling failures once per attempt
                logging.warning(f"Polling attempt {attempt + 1} failed: {e}")

            await asyncio.sleep(5)  # Wait 1 second before polling again

        # If no images are available after 10 seconds, return an error
        raise HTTPException(status_code=408, detail="Image generation timed out.")
    except Exception as e:
        logging.error(f"Error in generate_and_poll_images: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
# Generate and save to project
@router.post("/")
async def generate_and_save_image(request: GenerateAndSaveRequest, db: Session = Depends(get_db)):
    try:
        # Trigger image generation
        create_response = create_generation(
            prompt=request.prompt,
            height=request.height,
            width=request.width,
            num_images=request.num_images,
            preset_style=request.preset_style,
        )
        generation_id = create_response["sdGenerationJob"]["generationId"]

        # Poll for generated images
        images = None
        for attempt in range(10):  # Poll for up to 10 attempts
            try:
                images = get_generation(generation_id)
                if images:  # If images are available, break the polling loop
                    logging.info(f"Images found after {attempt + 1} attempts.")
                    break
            except Exception as e:
                # Log polling failures once per attempt
                logging.warning(f"Polling attempt {attempt + 1} failed: {e}")

            await asyncio.sleep(5)  # Wait 5 seconds before polling again

        if not images:
            raise HTTPException(status_code=408, detail="Image generation timed out.")

        # Save all generated images to the database
        saved_images = []
        for img in images:
            saved_image = save_image(
                db=db,
                id=img["id"],
                url=img["url"],
                project_id=request.project_id,
                prompt_artstyle=request.prompt_artstyle,
                prompt_scenery=request.prompt_scenery,
                prompt_actor=request.prompt_actor,
                type=request.type,
            )
            saved_images.append(saved_image)
        logging.info(f"Saved {len(saved_images)} images to the database.")
        return {
            "status": "success", 
            "data": images[0] if len(images) == 1 else images
        }
    except Exception as e:
        logging.error(f"Error in generate_and_save_image: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

class PromptRequest(BaseModel):
    prompt: str

@router.post("/improve")
async def improve_prompt_endpoint(prompt_request: PromptRequest):
    try:
        response = improve_prompt_api(prompt_request.prompt)
        return {"status": "success", "data": response}  
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
