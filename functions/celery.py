
from celery import Celery
from functions.leonardo import improve_prompt_api

# Create Celery app with memory broker for testing
celery_app = Celery(
    "fast_teller",
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


@celery_app.task(name="improve_prompt_task")
def improve_prompt_task(prompt: str):
    # This task wraps the synchronous API call
    result = improve_prompt_api(prompt)
    return result

