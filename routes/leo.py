import logging
from fastapi import APIRouter, HTTPException, Depends
from services.leo_common import get_generation, improve_prompt_api, delete_generation_api
from services.leo_image import create_generation,  poll_all_generations
from services.leo_video import create_video_generation
import asyncio
from pydantic import BaseModel
from schemas.leo import GenerateAndSaveRequest, GenerationRequest, GenVideoRequest
from services.image import save_image
from sqlalchemy.orm import Session
from typing import List
router = APIRouter(tags=["Leo"])
from database import get_db

    
# Dummy get to validate routing
@router.get("/")
async def root():
    return {"message": "Welcome to the Leonardo API"}

# Generate image
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

        for attempt in range(10):  
            try:
                images = get_generation(generation_id)
                if images:  
                    logging.info(f"Images found after {attempt + 1} attempts.")
                    return {"status": "success", "data": images, "gen": generation_id}
            except Exception as e:
                logging.warning(f"Polling attempt {attempt + 1} failed: {e}")

            await asyncio.sleep(5)  # Wait 5 seconds before polling again

        raise HTTPException(status_code=408, detail="Image generation timed out.")
    except Exception as e:
        logging.error(f"Error in generate_and_poll_images: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    
# Generate video
@router.post("/generate-video")
async def generate_video(request: GenVideoRequest):
    try:
        create_response = create_video_generation(
            prompt=request.prompt,
            image_id=request.imageId,
            image_type=request.imageType,
        )
        generation_id = create_response["motionVideoGenerationJob"]["generationId"]
        for attempt in range(10): 
            try:
                videos = get_generation(generation_id)
                if videos:  
                    logging.info(f"Videos found after {attempt + 1} attempts.")
                    return {"status": "success", "data": videos, "gen": generation_id}
            except Exception as e:
                logging.warning(f"Polling attempt {attempt + 1} failed: {e}")

            await asyncio.sleep(20)  
        raise HTTPException(status_code=408, detail="Video generation timed out.")
    except Exception as e:
        logging.error(f"Error in generate_video: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# New endpoint for parallel generation of multiple images
class BatchGenerationRequest(BaseModel):
    prompts: List[str]
    height: int = 600
    width: int = 600
    num_images: int = 1
    preset_style: str = "DYNAMIC"

@router.post("/generate-batch")
async def generate_batch_images(request: BatchGenerationRequest):
    """Generate multiple images in parallel based on different prompts"""
    try:
        if not request.prompts or len(request.prompts) == 0:
            raise HTTPException(status_code=400, detail="No prompts provided")
            
        # Create all generation jobs in parallel
        generation_tasks = []
        for prompt in request.prompts:
            generation_tasks.append(
                create_generation(
                    prompt=prompt,
                    height=request.height,
                    width=request.width,
                    num_images=request.num_images,
                    preset_style=request.preset_style,
                    # TBD constants for now
                    ultra=True,
                    contrast=3.5,
                )
            )
            
        # Gather all generation IDs
        generation_ids = []
        for i, task_result in enumerate(generation_tasks):
            generation_id = task_result["sdGenerationJob"]["generationId"]
            generation_ids.append({"id": generation_id, "prompt": request.prompts[i]})
            
        # Poll for all images concurrently with asyncio.gather
        poll_results = await poll_all_generations(generation_ids)
        
        # Return results
        return {"status": "success", "data": poll_results}
        
    except Exception as e:
        logging.error(f"Error in generate_batch_images: {e}", exc_info=True)
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
    
class SketchRequest(BaseModel):
    prompt: str

# @router.post("/sketch")
# async def sketch_images(request: SketchRequest):

    
class DeleteGenerationsRequest(BaseModel):
    generation_ids: list[str]

@router.post("/delete")
async def delete_generations(request: DeleteGenerationsRequest):
    try:  
        for generation_id in request.generation_ids:
            delete_generation_api(generation_id)
            logging.info(f"Deleted generation with ID: {generation_id}")
        return {"status": "success", "message": "Generations deleted successfully."}
    except Exception as e:
        logging.error(f"Error in delete_generations: {e}", exc_info=True)
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
