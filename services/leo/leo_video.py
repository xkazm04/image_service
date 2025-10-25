import requests
import os
from dotenv import load_dotenv
import logging
import asyncio
logging.basicConfig(level=logging.DEBUG)
from services.leo_common import get_generation

load_dotenv()

LEONARDO_API_BASE_URL = "https://cloud.leonardo.ai/api/rest/v1"
LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")

if not LEONARDO_API_KEY:
    raise ValueError("Leonardo API key is missing. Please set it in the .env file.")

HEADERS = {
    "Authorization": f"Bearer {LEONARDO_API_KEY}",
    "Content-Type": "application/json",
}

def create_video_generation(
        prompt: str, 
        image_id: str,
        image_type: int = 512, 
    ): 
    url = f"{LEONARDO_API_BASE_URL}/generations-image-to-video"
    payload = {
        "imageId": image_id,
        "imageType": image_type,
        "prompt": prompt,
        "promptEnhance": True,
    }
    try:
        logging.debug("Calling Leonardo API with payload: %s", payload)
        response = requests.post(url, json=payload, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error("Error calling Leonardo API: %s", e)
        raise
    
async def poll_video_generation(generation_id: str, prompt: str):
    """Poll for a single generation with timeout"""
    for attempt in range(10):
        try:
            vidoes = get_generation(generation_id)
            if vidoes:
                for vid in vidoes:
                    vid["prompt"] = prompt
                logging.info(f"Video found after {attempt + 1} attempts")
                return vidoes
        except Exception as e:
            logging.warning(f"Polling attempt {attempt + 1} for ID {generation_id} failed: {e}")
        
        await asyncio.sleep(20)
    
    raise Exception(f"Generation timed out for ID {generation_id}")