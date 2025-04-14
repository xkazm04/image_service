import logging
from fastapi import APIRouter, HTTPException, Query
from functions.leonardo import create_generation, get_generation, improve_prompt_api, remove_background_api, get_varation_by_id
import asyncio
from pydantic import BaseModel
from celery_config import monitor_background_removal

router = APIRouter(tags=["Leo"])

class GenerationRequest(BaseModel):
    prompt: str
    height: int = 512
    width: int = 512
    num_images: int = 4
    preset_style: str = "DYNAMIC"
    
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

class PromptRequest(BaseModel):
    prompt: str

@router.post("/improve")
async def improve_prompt_endpoint(prompt_request: PromptRequest):
    try:
        response = improve_prompt_api(prompt_request.prompt)
        return {"status": "success", "data": response}  
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/remove_background")
async def remove_background_endpoint(image_id: str = Query(..., description="The ID of the image to remove background from")):
    try:
        response = remove_background_api(image_id)
        job_id = response.get("data", {}).get("sdNobgJob", {}).get("id")
        
        if not job_id:
            raise HTTPException(status_code=500, detail="Failed to get job ID from Leonardo API")
        
        monitor_background_removal.delay(job_id)
        return {
            "status": "success", 
            "message": "Background removal process started", 
            "job_id": job_id,
            "data": response
        }
    except Exception as e:
        logging.error(f"Error in remove_background_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/variation/{image_id}")
async def get_variation(image_id: str):
    try:
        response = get_varation_by_id(image_id)
        return {"status": "success", "data": response}  
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

