from celery import Celery
import os
from dotenv import load_dotenv
import logging
from database import get_db
from functions.leonardo import get_varation_by_id, save_processed_image_url
import time

load_dotenv()

# Create Celery instance
celery_app = Celery(
    'fast-teller',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

# Configure Celery to use JSON instead of pickle for serialization
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    result_backend_transport_options={
        'visibility_timeout': 43200,  # 12 hours
    },
    worker_prefetch_multiplier=1,  # Process one task at a time
    task_track_started=True,
)

# Explicitly set the result backend to use redis instead of any custom backend
celery_app.conf.result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

@celery_app.task(bind=True, max_retries=20)  # Allow for multiple retries over a long period
def monitor_background_removal(self, job_id):
    """
    Monitor the background removal process until it completes.
    This task polls the Leonardo API at regular intervals to check the status.
    """
    try:
        logging.info(f"Starting background removal monitoring for job: {job_id}")
        
        # Initial delay before first check
        time.sleep(30)
        
        # Get a database session
        db = next(get_db())
        
        # Check status periodically
        max_attempts = 20
        for attempt in range(max_attempts):
            try:
                response = get_varation_by_id(job_id)
                
                # Check if we have a completed result
                images = response.get('data', {}).get('generated_image_variation_generic', [])
                
                for image in images:
                    if image.get('status') == 'COMPLETE' and image.get('id') == job_id:
                        url = image.get('url')
                        if url:
                            # Save the processed image URL to the database
                            save_processed_image_url(job_id, url, db)
                            logging.info(f"Background removal complete for job {job_id}, URL saved: {url}")
                            return {"status": "success", "job_id": job_id, "url": url}
                
                # If not complete, wait and retry
                logging.info(f"Job {job_id} not complete yet, attempt {attempt+1}/{max_attempts}")
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logging.error(f"Error checking background removal status: {e}")
                time.sleep(60)  # Wait longer after an error
        
        # If we get here, the process didn't complete within expected time
        logging.warning(f"Background removal job {job_id} did not complete after {max_attempts} attempts")
        return {"status": "timeout", "job_id": job_id}
        
    except Exception as e:
        logging.error(f"Unexpected error in monitor_background_removal task: {e}")
        raise self.retry(exc=e, countdown=60)  # Retry after 60 seconds
    finally:
        # Close the database session
        db.close()
