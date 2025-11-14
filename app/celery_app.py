from celery import Celery
from app.config import settings

# Creating the Celery app - our async task processing powerhouse
celery_app = Celery(
    "product_importer",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.import_tasks"]
)

# Celery configuration - tuning it for optimal performance
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,  # Track when tasks start (useful for progress)
    task_time_limit=3600,  # 1 hour max per task (for those massive CSV files)
    worker_prefetch_multiplier=1,  # Process one task at a time per worker
)

