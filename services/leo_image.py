import requests
import os
from dotenv import load_dotenv
import logging
import asyncio
from services.leo_common import get_generation
logging.basicConfig(level=logging.DEBUG)

load_dotenv()

LEONARDO_API_BASE_URL = "https://cloud.leonardo.ai/api/rest/v1"
LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")

if not LEONARDO_API_KEY:
    raise ValueError("Leonardo API key is missing. Please set it in the .env file.")

HEADERS = {
    "Authorization": f"Bearer {LEONARDO_API_KEY}",
    "Content-Type": "application/json",
}

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

async def poll_single_generation(generation_id: str, prompt: str):
    """Poll for a single generation with timeout"""
    for attempt in range(10):
        try:
            images = get_generation(generation_id)
            if images:
                # Add the prompt to the response for client-side matching
                for img in images:
                    img["prompt"] = prompt
                logging.info(f"Images for '{prompt[:30]}...' found after {attempt + 1} attempts")
                return images
        except Exception as e:
            logging.warning(f"Polling attempt {attempt + 1} for ID {generation_id} failed: {e}")
        
        await asyncio.sleep(5)
    
    raise Exception(f"Generation timed out for ID {generation_id}")