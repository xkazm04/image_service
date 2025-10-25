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