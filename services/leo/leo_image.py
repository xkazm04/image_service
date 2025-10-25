import requests
import os
from dotenv import load_dotenv
import logging
import asyncio
from services.leo_common import get_generation
from utils.storage import LocalStorage
import uuid

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

LEONARDO_API_BASE_URL = "https://cloud.leonardo.ai/api/rest/v1"
LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")

if not LEONARDO_API_KEY:
    raise ValueError("Leonardo API key is missing. Please set it in the .env file.")

HEADERS = {
    "Authorization": f"Bearer {LEONARDO_API_KEY}",
    "Content-Type": "application/json",
}

# Initialize local storage
storage = LocalStorage()

def create_generation(
        prompt: str, 
        height: int = 512, 
        width: int = 512, 
        model: str = "de7d3faf-762f-48e0-b3b7-9d0ac3a3fcf3", # Phoenix 1.0 Leonardo
        num_images: int = 4, 
        preset_style: str = "DYNAMIC"): # SKETCH_BW, CREATIVE, PHOTOGRAPHY
    url = f"{LEONARDO_API_BASE_URL}/generations"
    payload = {
        "alchemy": True,
        "height": height,
        "width": width,
        "modelId": model,
        "presetStyle": preset_style,
        "prompt": prompt,
        "num_images": num_images,
    }
    try:
        logging.debug("Calling Leonardo API with payload: %s", payload)
        response = requests.post(url, json=payload, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error("Error calling Leonardo API: %s", e)
        raise

def sketch_api(prompt: str):
    """Generate a sketch using the Leonardo API."""
    url = f"{LEONARDO_API_BASE_URL}/generations"
    payload = {
        "alchemy": True,
        "height": 250,
        "width": 250,
        "modelId": "de7d3faf-762f-48e0-b3b7-9d0ac3a3fcf3",
        "presetStyle": "SKETCH_BW",
        "prompt": prompt,
        "num_images": 1,
    }
    try:
        logging.debug("Calling Leonardo API with payload: %s", payload)
        response = requests.post(url, json=payload, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        logging.info("Sketch generated successfully.")
        return data
    except requests.exceptions.RequestException as e:
        logging.error("Error calling Leonardo API: %s", e)
        raise



async def poll_all_generations(generation_ids):
    """Poll for multiple generations concurrently"""
    poll_tasks = []
    
    for gen in generation_ids:
        poll_tasks.append(poll_single_generation(gen["id"], gen["prompt"]))
        
    results = await asyncio.gather(*poll_tasks, return_exceptions=True)
    
    # Filter out any error results
    valid_results = []
    for result in results:
        if isinstance(result, Exception):
            logging.error(f"Generation error: {result}")
        else:
            valid_results.append(result)
            
    return valid_results

async def poll_single_generation(generation_id: str, prompt: str, project_id: str = None):
    """Poll for a single generation with timeout and save images locally"""
    for attempt in range(10):
        try:
            images = get_generation(generation_id)
            if images:
                # Download and save images locally if project_id is provided
                if project_id:
                    for img in images:
                        image_id = img["id"]
                        image_url = img["url"]
                        
                        # Download and save the image locally
                        local_path = storage.download_and_save_image(
                            image_url, project_id, image_id
                        )
                        
                        if local_path:
                            # Update the URL to point to local file
                            img["local_path"] = local_path
                            img["local_url"] = storage.get_image_url(project_id, image_id)
                        
                        img["prompt"] = prompt
                
                logger.info(f"Images for '{prompt[:30]}...' found after {attempt + 1} attempts")
                return images
        except Exception as e:
            logger.warning(f"Polling attempt {attempt + 1} for ID {generation_id} failed: {e}")
        
        await asyncio.sleep(5)
    
    raise Exception(f"Generation timed out for ID {generation_id}")

def generate_and_save_locally(
    prompt: str,
    project_id: str,
    height: int = 512,
    width: int = 512,
    model: str = "de7d3faf-762f-48e0-b3b7-9d0ac3a3fcf3",
    num_images: int = 4,
    preset_style: str = "DYNAMIC"
):
    """Generate images and automatically save them locally"""
    try:
        # Create the generation
        response = create_generation(
            prompt=prompt,
            height=height,
            width=width,
            model=model,
            num_images=num_images,
            preset_style=preset_style
        )
        
        generation_id = response.get("sdGenerationJob", {}).get("generationId")
        if not generation_id:
            raise Exception("Failed to get generation ID from Leonardo API")
        
        logger.info(f"Started generation {generation_id} for project {project_id}")
        
        return {
            "generation_id": generation_id,
            "project_id": project_id,
            "prompt": prompt,
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Failed to start generation: {e}")
        raise