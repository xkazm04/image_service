from celery import Celery
import os
from database import SessionLocal # Import SessionLocal
from functions.image import delete_unsaved_images # Import the function

# Create Celery app with memory broker for testing
celery_app = Celery(
    "image:_service",
    broker="memory://",  # Use memory broker for testing without Redis
    backend="memory://"
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Add broker_connection_retry and broker_connection_retry_on_startup options
    broker_connection_retry=True,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
)

@celery_app.task(name="long_running_task")
def long_running_task(data):
    # Simulate long processing
    import time
    time.sleep(60)
    return f"Processed: {data}"


# Define the cleanup task
@celery_app.task(name="cleanup_unsaved_images")
def cleanup_unsaved_images_task():
    """Celery task to delete unsaved images."""
    db = SessionLocal()
    try:
        print("Running scheduled task: delete_unsaved_images")
        delete_unsaved_images(db)
        print("Finished scheduled task: delete_unsaved_images")
    except Exception as e:
        print(f"Error during scheduled cleanup: {e}")
        # Optionally re-raise or handle specific exceptions
    finally:
        db.close()

# Configure Celery Beat schedule
celery_app.conf.beat_schedule = {
    'delete-unsaved-images-hourly': {
        'task': 'cleanup_unsaved_images',
        # 'schedule': crontab(minute=0),  # Runs every hour at minute 0
        'schedule': 3600.0, # Runs every 3600 seconds (1 hour) - simpler alternative
        # Add arguments if your task needs them, e.g.:
        # 'args': (arg1, arg2),
    },
    # ... other scheduled tasks if any ...
}
celery_app.conf.timezone = 'UTC' # Optional: Set timezone

# TBD Redis / celery -A functions.celery beat -l info