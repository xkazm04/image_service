
import logging
from fastapi import APIRouter, HTTPException
from services.leo_variation import remove_background_api, get_varation_by_id, upscale_api
from pydantic import BaseModel
from celery_config import monitor_background_removal
router = APIRouter(tags=["Variants"])

class EditImage(BaseModel):
    image_id: str
    

@router.post("/nobg")
async def remove_background_endpoint(request: EditImage):
    try:
        response = remove_background_api(request.image_id)
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
    
@router.post("/upscale")
async def upscale_endpoint(request: EditImage):
    try:
        response = upscale_api(request.image_id)
        job_id = response.get("data", {}).get("sdUpscaleJob", {}).get("id")
        
        if not job_id:
            raise HTTPException(status_code=500, detail="Failed to get job ID from Leonardo API")
        
        monitor_background_removal.delay(job_id)
        return {
            "status": "success", 
            "message": "Upscaling process started", 
            "job_id": job_id,
            "data": response
        }
    except Exception as e:
        logging.error(f"Error in upscale_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/unzoom")
async def unzoom_endpoint(request: EditImage):
    try:
        response = upscale_api(request.image_id)
        job_id = response.get("data", {}).get("sdUnzoomJob", {}).get("id")
        
        if not job_id:
            raise HTTPException(status_code=500, detail="Failed to get job ID from Leonardo API")
        
        monitor_background_removal.delay(job_id)
        return {
            "status": "success", 
            "message": "Unzoom process started", 
            "job_id": job_id,
            "data": response
        }
    except Exception as e:
        logging.error(f"Error in unzoom_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/variation/{image_id}")
async def get_variation(image_id: str):
    try:
        response = get_varation_by_id(image_id)
        return {"status": "success", "data": response}  
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))