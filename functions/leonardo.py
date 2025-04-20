import requests
import os
from dotenv import load_dotenv
import logging
from models.models import Image

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

def delete_generation_api(generation_id: str):
    """Delete a generation by its ID."""
    url = f"{LEONARDO_API_BASE_URL}/generations/{generation_id}"
    try:
        response = requests.delete(url, headers=HEADERS)
        response.raise_for_status()
        logging.info("Generation deleted successfully.")
    except requests.exceptions.RequestException as e:
        logging.error("Error deleting generation: %s", e)
        raise


def get_generation(generation_id: str):
    """Retrieve generated images based on generation_id."""
    url = f"{LEONARDO_API_BASE_URL}/generations/{generation_id}"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        generated_images = data["generations_by_pk"]["generated_images"]
        return [
            {
                "url": image["url"],
                "id": image["id"],
                "nsfw": image["nsfw"],
            }
            for image in generated_images
        ]
    except requests.exceptions.RequestException as e:
        logging.error("Error fetching generated images: %s", e)
        raise
    
def improve_prompt_api(prompt: str):
    """Improve the prompt by calling Leonardo AI API."""
    url = f"{LEONARDO_API_BASE_URL}/prompt/improve"
    payload = {
        "prompt": prompt,
    }

    response = requests.post(url, json=payload, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    return data

def remove_background_api(image_id: str):
    """Remove the background from an image."""
    url = f"{LEONARDO_API_BASE_URL}/variations/nobg"
    payload = {
        "id": image_id,
    }
    response = requests.post(url, json=payload, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    return data

def upscale_api(image_id: str):
    """Remove the background from an image."""
    url = f"{LEONARDO_API_BASE_URL}/variations/upscale"
    payload = {
        "id": image_id,
    }
    response = requests.post(url, json=payload, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    return data

def unzoom_api(image_id: str):
    """Unzoom an image."""
    url = f"{LEONARDO_API_BASE_URL}/variations/unzoom"
    payload = {
        "id": image_id,
    }
    response = requests.post(url, json=payload, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    return data

def get_varation_by_id(job_id: str):
    """Get variation by image ID."""
    url = f"{LEONARDO_API_BASE_URL}/variations/{job_id}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    return data

def save_processed_image_url(image_id: str, url: str, db_session):
    """Save the processed image URL to the database."""
    try:
        image = db_session.query(Image).filter(Image.leo_id == image_id).first()
        if image:
            image.assigned_image_url = url
            db_session.commit()
            logging.info(f"Updated image {image_id} with processed URL: {url}")
            return True
        else:
            logging.warning(f"Image with ID {image_id} not found in database")
            return False
    except Exception as e:
        logging.error(f"Error saving processed image URL: {e}")
        db_session.rollback()
        raise

# Response object 
# {
#     "status": "success",
#     "data": {
#         "generated_image_variation_generic": [
#             {
#                 "url": "https://cdn.leonardo.ai/users/65d71243-f7c2-4204-a1b3-433aaf62da5b/generations/5e126f6c-2601-4224-af18-92eb3f5fa5cb/variations/Default_In_this_compelling_scene_the_dialogue_between_Jedi_Mas_2_5e126f6c-2601-4224-af18-92eb3f5fa5cb_0.png",
#                 "status": "COMPLETE",
#                 "id": "5e126f6c-2601-4224-af18-92eb3f5fa5cb",
#                 "createdAt": "2025-03-27T20:17:55.833",
#                 "transformType": "NOBG"
#             }
#         ]
#     }
# }