import json
import redis
from celery import Task
from app.celery_app import celery_app
from app.database import SessionLocal
from app.services.csv_processor import CSVProcessor
from app.config import settings


class ProgressTask(Task):
    """
    Custom Celery task class that tracks progress.
    Updates Redis with progress information for real-time monitoring.
    """
    
    def update_progress(self, current: int, total: int, message: str):
        """Update progress in Redis - the progress tracker's best friend."""
        if self.request.id:
            redis_client = redis.from_url(settings.REDIS_URL)
            progress_data = {
                "current": current,
                "total": total,
                "percentage": int((current / total * 100)) if total > 0 else 0,
                "message": message,
                "status": "processing"
            }
            redis_client.setex(
                f"upload_progress:{self.request.id}",
                3600,  # Expire after 1 hour
                json.dumps(progress_data)
            )


@celery_app.task(base=ProgressTask, bind=True, name="import_csv_task")
def import_csv_task(self, csv_content: str):
    """
    Celery task to import products from CSV content.
    This runs asynchronously so the API doesn't timeout on large files.
    """
    db = SessionLocal()
    
    try:
        # Initial progress update
        self.update_progress(0, 0, "Starting CSV processing...")
        
        # Progress callback that updates Redis
        def progress_callback(current: int, total: int, message: str):
            try:
                self.update_progress(current, total, message)
            except Exception as e:
                # Don't let progress callback errors break the import
                print(f"Progress update error: {e}")
        
        # Create processor and process the CSV
        processor = CSVProcessor(db, progress_callback=progress_callback)
        result = processor.process_csv(csv_content, chunk_size=1000)
        
        # Update final status
        redis_client = redis.from_url(settings.REDIS_URL)
        final_data = {
            "current": result["processed"],
            "total": result["total_rows"],
            "percentage": 100,
            "message": result["message"],
            "status": "completed" if result["success"] else "failed",
            "errors": result.get("errors", []),
            "error_count": result.get("error_count", 0)
        }
        redis_client.setex(
            f"upload_progress:{self.request.id}",
            3600,
            json.dumps(final_data)
        )
        
        return {
            "task_id": self.request.id,
            "success": result["success"],
            "processed": result["processed"],
            "total_rows": result["total_rows"],
            "errors": result.get("errors", []),
            "error_count": result.get("error_count", 0)
        }
    
    except Exception as e:
        # Handle errors gracefully
        redis_client = redis.from_url(settings.REDIS_URL)
        error_data = {
            "status": "failed",
            "message": str(e),
            "error": "An error occurred during CSV processing"
        }
        redis_client.setex(
            f"upload_progress:{self.request.id}",
            3600,
            json.dumps(error_data)
        )
        raise
    
    finally:
        db.close() # Cleanup after ourselves :Thumb_up:

