import json
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from app.tasks.import_tasks import import_csv_task
from app.config import settings
import redis
import asyncio

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post("")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload a CSV file for processing.
    Returns a task ID that can be used to track progress.
    Because waiting for 500,000 rows to process would make anyone impatient!
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV file")
    
    # Read file content
    try:
        content = await file.read()
        csv_content = content.decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    
    if not csv_content.strip():
        raise HTTPException(status_code=400, detail="CSV file is empty")
    
    # Start async task
    task = import_csv_task.delay(csv_content)
    
    return {
        "task_id": task.id,
        "message": "CSV upload started. Use the task_id to check progress.",
        "status": "processing"
    }


@router.get("/status/{task_id}")
def get_upload_status(task_id: str):
    """
    Get upload progress by polling Redis.
    Perfect for those who prefer checking in rather than streaming.
    """
    redis_client = redis.from_url(settings.REDIS_URL)
    progress_key = f"upload_progress:{task_id}"
    
    progress_data = redis_client.get(progress_key)
    
    if not progress_data:
        # Check if task exists in Celery
        task_result = import_csv_task.AsyncResult(task_id)
        if task_result.state == "PENDING":
            return {
                "task_id": task_id,
                "status": "pending",
                "message": "Task not found or not started"
            }
        elif task_result.state == "FAILURE":
            return {
                "task_id": task_id,
                "status": "failed",
                "message": "Task failed",
                "error": str(task_result.info)
            }
        else:
            return {
                "task_id": task_id,
                "status": "unknown",
                "message": "Progress data not available"
            }
    
    try:
        progress = json.loads(progress_data)
        return {
            "task_id": task_id,
            **progress
        }
    except json.JSONDecodeError:
        return {
            "task_id": task_id,
            "status": "error",
            "message": "Error parsing progress data"
        }


@router.get("/stream/{task_id}")
async def stream_upload_progress(task_id: str):
    """
    Server-Sent Events (SSE) endpoint for real-time progress updates.
    The streaming experience - watch your upload progress in real-time!
    """
    redis_client = redis.from_url(settings.REDIS_URL)
    progress_key = f"upload_progress:{task_id}"
    
    async def event_generator():
        last_status = None
        
        while True:
            progress_data = redis_client.get(progress_key)
            
            if progress_data:
                try:
                    progress = json.loads(progress_data)
                    current_status = progress.get("status")
                    
                    # Send update if status changed or periodically
                    if progress != last_status:
                        yield f"data: {json.dumps(progress)}\n\n"
                        last_status = progress
                        
                        # Stop if completed or failed
                        if current_status in ["completed", "failed"]:
                            break
                except json.JSONDecodeError:
                    yield f"data: {json.dumps({'status': 'error', 'message': 'Error parsing progress'})}\n\n"
                    break
            else:
                # Check Celery task status
                task_result = import_csv_task.AsyncResult(task_id)
                if task_result.state == "FAILURE":
                    yield f"data: {json.dumps({'status': 'failed', 'message': str(task_result.info)})}\n\n"
                    break
                elif task_result.state == "SUCCESS":
                    yield f"data: {json.dumps({'status': 'completed', 'message': 'Task completed'})}\n\n"
                    break
            
            # Wait before next check
            await asyncio.sleep(1)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

