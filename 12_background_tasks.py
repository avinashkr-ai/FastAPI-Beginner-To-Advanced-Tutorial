"""
FastAPI Advanced Level - File 12: Background Tasks and Async Operations
=====================================================================

This file covers advanced asynchronous programming concepts in FastAPI including:
- Background tasks execution
- Async/await patterns
- Task queues and job scheduling
- Email sending and notifications
- File processing in background
- Database cleanup tasks
- Periodic task scheduling
- Task status monitoring
- Error handling in background tasks
- Performance optimization

Background tasks allow you to run operations after returning a response,
which is perfect for operations that don't need to block the user.
"""

from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
import asyncio
import aiofiles
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import uuid
import time
from datetime import datetime, timedelta
import logging
from pathlib import Path
import os
from contextlib import asynccontextmanager
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================================================
# 1. TASK MODELS AND CONFIGURATION
# ==================================================

@dataclass
class TaskStatus:
    """
    Task status tracking with metadata
    """
    task_id: str
    status: str = "pending"  # pending, running, completed, failed
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

# In-memory task storage (use Redis in production)
task_storage: Dict[str, TaskStatus] = {}

class EmailRequest(BaseModel):
    """
    Email sending request model
    """
    to: EmailStr
    subject: str
    body: str
    cc: Optional[List[EmailStr]] = []
    bcc: Optional[List[EmailStr]] = []

class FileProcessRequest(BaseModel):
    """
    File processing request model
    """
    file_path: str
    operation: str  # resize, convert, compress, etc.
    parameters: Dict[str, Any] = {}

class ReportRequest(BaseModel):
    """
    Report generation request model
    """
    report_type: str
    date_range: Dict[str, str]
    format: str = "pdf"
    include_charts: bool = True

# ==================================================
# 2. BACKGROUND TASK UTILITIES
# ==================================================

def create_task_id() -> str:
    """
    Generate unique task ID
    """
    return str(uuid.uuid4())

def update_task_status(task_id: str, status: str, **kwargs):
    """
    Update task status with additional metadata
    """
    if task_id in task_storage:
        task = task_storage[task_id]
        task.status = status
        
        # Update timestamps
        if status == "running" and not task.started_at:
            task.started_at = datetime.now()
        elif status in ["completed", "failed"]:
            task.completed_at = datetime.now()
        
        # Update other fields
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        logger.info(f"Task {task_id} status updated to {status}")

async def log_task_completion(task_id: str, result: Any = None, error: str = None):
    """
    Log task completion with results or errors
    """
    if error:
        logger.error(f"Task {task_id} failed: {error}")
        update_task_status(task_id, "failed", error=error)
    else:
        logger.info(f"Task {task_id} completed successfully")
        update_task_status(task_id, "completed", result=result)

# ==================================================
# 3. EMAIL BACKGROUND TASKS
# ==================================================

async def send_email_task(email_request: EmailRequest, task_id: str):
    """
    Background task to send email
    This simulates actual email sending (replace with real SMTP in production)
    """
    try:
        update_task_status(task_id, "running", progress=0.1)
        
        # Simulate email composition
        await asyncio.sleep(1)
        update_task_status(task_id, "running", progress=0.3)
        
        # Simulate SMTP connection
        await asyncio.sleep(1)
        update_task_status(task_id, "running", progress=0.6)
        
        # Simulate email sending
        await asyncio.sleep(1)
        update_task_status(task_id, "running", progress=0.9)
        
        # In production, use real SMTP:
        # smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
        # smtp_server.starttls()
        # smtp_server.login(username, password)
        # smtp_server.send_message(message)
        # smtp_server.quit()
        
        result = {
            "message": "Email sent successfully",
            "to": email_request.to,
            "subject": email_request.subject,
            "sent_at": datetime.now().isoformat()
        }
        
        await log_task_completion(task_id, result)
        
    except Exception as e:
        await log_task_completion(task_id, error=str(e))

def send_notification_email(user_email: str, message: str, task_id: str):
    """
    Synchronous email sending for simple notifications
    """
    try:
        logger.info(f"Sending notification to {user_email}: {message}")
        # Simulate email sending delay
        time.sleep(0.5)
        
        result = {
            "email": user_email,
            "message": message,
            "sent_at": datetime.now().isoformat()
        }
        
        update_task_status(task_id, "completed", result=result)
        
    except Exception as e:
        update_task_status(task_id, "failed", error=str(e))

# ==================================================
# 4. FILE PROCESSING BACKGROUND TASKS
# ==================================================

async def process_file_task(file_request: FileProcessRequest, task_id: str):
    """
    Background task for file processing operations
    """
    try:
        update_task_status(task_id, "running", progress=0.1)
        
        file_path = Path(file_request.file_path)
        
        # Validate file exists
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        update_task_status(task_id, "running", progress=0.2)
        
        # Simulate different file operations
        operation = file_request.operation
        
        if operation == "resize":
            await resize_image_task(file_path, file_request.parameters, task_id)
        elif operation == "convert":
            await convert_file_task(file_path, file_request.parameters, task_id)
        elif operation == "compress":
            await compress_file_task(file_path, file_request.parameters, task_id)
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        result = {
            "operation": operation,
            "file_path": str(file_path),
            "parameters": file_request.parameters,
            "processed_at": datetime.now().isoformat()
        }
        
        await log_task_completion(task_id, result)
        
    except Exception as e:
        await log_task_completion(task_id, error=str(e))

async def resize_image_task(file_path: Path, parameters: Dict, task_id: str):
    """
    Simulate image resizing operation
    """
    width = parameters.get("width", 800)
    height = parameters.get("height", 600)
    
    logger.info(f"Resizing image {file_path} to {width}x{height}")
    
    # Simulate processing stages
    for progress in [0.3, 0.5, 0.7, 0.9]:
        await asyncio.sleep(0.5)
        update_task_status(task_id, "running", progress=progress)
    
    # In production, use PIL or similar:
    # from PIL import Image
    # image = Image.open(file_path)
    # resized = image.resize((width, height))
    # resized.save(output_path)

async def convert_file_task(file_path: Path, parameters: Dict, task_id: str):
    """
    Simulate file format conversion
    """
    target_format = parameters.get("format", "pdf")
    
    logger.info(f"Converting file {file_path} to {target_format}")
    
    # Simulate conversion process
    for progress in [0.4, 0.6, 0.8, 1.0]:
        await asyncio.sleep(0.8)
        update_task_status(task_id, "running", progress=progress)

async def compress_file_task(file_path: Path, parameters: Dict, task_id: str):
    """
    Simulate file compression
    """
    compression_level = parameters.get("level", 5)
    
    logger.info(f"Compressing file {file_path} with level {compression_level}")
    
    # Simulate compression process
    for progress in [0.25, 0.5, 0.75, 1.0]:
        await asyncio.sleep(0.3)
        update_task_status(task_id, "running", progress=progress)

# ==================================================
# 5. REPORT GENERATION BACKGROUND TASKS
# ==================================================

async def generate_report_task(report_request: ReportRequest, task_id: str):
    """
    Background task for report generation
    """
    try:
        update_task_status(task_id, "running", progress=0.1)
        
        # Simulate data collection
        await asyncio.sleep(1)
        update_task_status(task_id, "running", progress=0.3)
        
        # Simulate data processing
        await asyncio.sleep(2)
        update_task_status(task_id, "running", progress=0.6)
        
        # Simulate report generation
        await asyncio.sleep(1.5)
        update_task_status(task_id, "running", progress=0.9)
        
        # Generate report file
        report_filename = f"report_{task_id}.{report_request.format}"
        report_path = Path(f"reports/{report_filename}")
        
        # Ensure reports directory exists
        report_path.parent.mkdir(exist_ok=True)
        
        # Simulate writing report file
        async with aiofiles.open(report_path, 'w') as f:
            await f.write(f"Generated report for {report_request.report_type}\n")
            await f.write(f"Date range: {report_request.date_range}\n")
            await f.write(f"Generated at: {datetime.now().isoformat()}\n")
        
        result = {
            "report_type": report_request.report_type,
            "file_path": str(report_path),
            "format": report_request.format,
            "date_range": report_request.date_range,
            "generated_at": datetime.now().isoformat()
        }
        
        await log_task_completion(task_id, result)
        
    except Exception as e:
        await log_task_completion(task_id, error=str(e))

# ==================================================
# 6. DATABASE CLEANUP BACKGROUND TASKS
# ==================================================

async def database_cleanup_task(task_id: str):
    """
    Background task for database maintenance
    """
    try:
        update_task_status(task_id, "running", progress=0.1)
        
        # Simulate cleanup operations
        cleanup_operations = [
            "Removing expired sessions",
            "Cleaning up temporary files",
            "Archiving old logs",
            "Optimizing database indexes",
            "Updating statistics"
        ]
        
        total_operations = len(cleanup_operations)
        
        for i, operation in enumerate(cleanup_operations):
            logger.info(f"Executing: {operation}")
            await asyncio.sleep(1)  # Simulate work
            
            progress = (i + 1) / total_operations * 0.9
            update_task_status(task_id, "running", progress=progress)
        
        result = {
            "operations_completed": cleanup_operations,
            "cleanup_at": datetime.now().isoformat(),
            "records_cleaned": 1250  # Example number
        }
        
        await log_task_completion(task_id, result)
        
    except Exception as e:
        await log_task_completion(task_id, error=str(e))

# ==================================================
# 7. PERIODIC TASKS AND SCHEDULING
# ==================================================

class TaskScheduler:
    """
    Simple task scheduler for periodic operations
    """
    
    def __init__(self):
        self.scheduled_tasks: List[Dict] = []
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def schedule_periodic_task(self, task_func, interval_seconds: int, task_name: str):
        """
        Schedule a task to run periodically
        """
        task_info = {
            "func": task_func,
            "interval": interval_seconds,
            "name": task_name,
            "last_run": None,
            "next_run": datetime.now() + timedelta(seconds=interval_seconds)
        }
        
        self.scheduled_tasks.append(task_info)
        logger.info(f"Scheduled periodic task: {task_name} (every {interval_seconds}s)")
    
    async def run_scheduler(self):
        """
        Run the task scheduler
        """
        while True:
            current_time = datetime.now()
            
            for task in self.scheduled_tasks:
                if current_time >= task["next_run"]:
                    task_id = create_task_id()
                    task_storage[task_id] = TaskStatus(
                        task_id=task_id,
                        metadata={"scheduled_task": task["name"]}
                    )
                    
                    logger.info(f"Running scheduled task: {task['name']}")
                    
                    # Run task in background
                    asyncio.create_task(task["func"](task_id))
                    
                    # Update scheduling info
                    task["last_run"] = current_time
                    task["next_run"] = current_time + timedelta(seconds=task["interval"])
            
            await asyncio.sleep(10)  # Check every 10 seconds

# Global scheduler instance
scheduler = TaskScheduler()

# ==================================================
# 8. FASTAPI APPLICATION SETUP
# ==================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management
    Start background scheduler when app starts
    """
    # Schedule periodic tasks
    scheduler.schedule_periodic_task(
        database_cleanup_task,
        interval_seconds=3600,  # Every hour
        task_name="database_cleanup"
    )
    
    # Start scheduler in background
    scheduler_task = asyncio.create_task(scheduler.run_scheduler())
    
    yield
    
    # Clean up when app shuts down
    scheduler_task.cancel()

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Background Tasks Demo",
    description="Comprehensive background task implementation examples",
    version="1.0.0",
    lifespan=lifespan
)

# ==================================================
# 9. API ENDPOINTS
# ==================================================

@app.post("/send-email")
async def send_email(email_request: EmailRequest, background_tasks: BackgroundTasks):
    """
    Send email in background
    Returns immediately with task ID for tracking
    """
    task_id = create_task_id()
    
    # Store task info
    task_storage[task_id] = TaskStatus(
        task_id=task_id,
        metadata={"type": "email", "to": email_request.to}
    )
    
    # Add background task
    background_tasks.add_task(send_email_task, email_request, task_id)
    
    return {
        "message": "Email sending started",
        "task_id": task_id,
        "status": "queued"
    }

@app.post("/send-notification")
async def send_notification(
    user_email: str,
    message: str,
    background_tasks: BackgroundTasks
):
    """
    Send simple notification email
    """
    task_id = create_task_id()
    
    task_storage[task_id] = TaskStatus(
        task_id=task_id,
        metadata={"type": "notification", "email": user_email}
    )
    
    # Add synchronous background task
    background_tasks.add_task(send_notification_email, user_email, message, task_id)
    
    return {
        "message": "Notification queued",
        "task_id": task_id
    }

@app.post("/process-file")
async def process_file(file_request: FileProcessRequest, background_tasks: BackgroundTasks):
    """
    Process file in background
    """
    task_id = create_task_id()
    
    task_storage[task_id] = TaskStatus(
        task_id=task_id,
        metadata={"type": "file_processing", "operation": file_request.operation}
    )
    
    background_tasks.add_task(process_file_task, file_request, task_id)
    
    return {
        "message": "File processing started",
        "task_id": task_id,
        "operation": file_request.operation
    }

@app.post("/generate-report")
async def generate_report(report_request: ReportRequest, background_tasks: BackgroundTasks):
    """
    Generate report in background
    """
    task_id = create_task_id()
    
    task_storage[task_id] = TaskStatus(
        task_id=task_id,
        metadata={"type": "report_generation", "report_type": report_request.report_type}
    )
    
    background_tasks.add_task(generate_report_task, report_request, task_id)
    
    return {
        "message": "Report generation started",
        "task_id": task_id,
        "report_type": report_request.report_type
    }

@app.post("/cleanup-database")
async def cleanup_database(background_tasks: BackgroundTasks):
    """
    Run database cleanup in background
    """
    task_id = create_task_id()
    
    task_storage[task_id] = TaskStatus(
        task_id=task_id,
        metadata={"type": "database_cleanup"}
    )
    
    background_tasks.add_task(database_cleanup_task, task_id)
    
    return {
        "message": "Database cleanup started",
        "task_id": task_id
    }

@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """
    Get status of a background task
    """
    if task_id not in task_storage:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )
    
    task = task_storage[task_id]
    
    return {
        "task_id": task.task_id,
        "status": task.status,
        "progress": task.progress,
        "created_at": task.created_at.isoformat(),
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "result": task.result,
        "error": task.error,
        "metadata": task.metadata
    }

@app.get("/tasks")
async def list_tasks(status: Optional[str] = None, limit: int = 50):
    """
    List all background tasks with optional filtering
    """
    tasks = list(task_storage.values())
    
    # Filter by status if provided
    if status:
        tasks = [task for task in tasks if task.status == status]
    
    # Sort by creation time (newest first)
    tasks.sort(key=lambda x: x.created_at, reverse=True)
    
    # Limit results
    tasks = tasks[:limit]
    
    return {
        "tasks": [
            {
                "task_id": task.task_id,
                "status": task.status,
                "progress": task.progress,
                "created_at": task.created_at.isoformat(),
                "metadata": task.metadata
            }
            for task in tasks
        ],
        "total": len(task_storage),
        "filtered": len(tasks)
    }

@app.delete("/task/{task_id}")
async def cancel_task(task_id: str):
    """
    Cancel/remove a task (for completed/failed tasks)
    """
    if task_id not in task_storage:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )
    
    task = task_storage[task_id]
    
    if task.status == "running":
        return JSONResponse(
            status_code=409,
            content={"message": "Cannot cancel running task"}
        )
    
    del task_storage[task_id]
    
    return {"message": f"Task {task_id} removed"}

# ==================================================
# 10. ADVANCED ASYNC PATTERNS
# ==================================================

@app.post("/batch-process")
async def batch_process(
    file_paths: List[str],
    operation: str,
    background_tasks: BackgroundTasks
):
    """
    Process multiple files concurrently
    """
    batch_task_id = create_task_id()
    individual_task_ids = []
    
    # Create individual tasks for each file
    for file_path in file_paths:
        task_id = create_task_id()
        individual_task_ids.append(task_id)
        
        task_storage[task_id] = TaskStatus(
            task_id=task_id,
            metadata={"type": "file_processing", "batch_id": batch_task_id}
        )
        
        file_request = FileProcessRequest(
            file_path=file_path,
            operation=operation
        )
        
        background_tasks.add_task(process_file_task, file_request, task_id)
    
    # Create batch tracking task
    task_storage[batch_task_id] = TaskStatus(
        task_id=batch_task_id,
        metadata={
            "type": "batch_processing",
            "individual_tasks": individual_task_ids,
            "total_files": len(file_paths)
        }
    )
    
    return {
        "message": "Batch processing started",
        "batch_task_id": batch_task_id,
        "individual_tasks": individual_task_ids,
        "total_files": len(file_paths)
    }

@app.get("/async-demo")
async def async_demo():
    """
    Demonstrate async operations running concurrently
    """
    # Run multiple operations concurrently
    tasks = [
        asyncio.create_task(slow_operation("Task 1", 1)),
        asyncio.create_task(slow_operation("Task 2", 2)),
        asyncio.create_task(slow_operation("Task 3", 0.5))
    ]
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks)
    
    return {
        "message": "All async operations completed",
        "results": results,
        "total_time": "About 2 seconds (concurrent execution)"
    }

async def slow_operation(name: str, duration: float):
    """
    Simulate slow async operation
    """
    await asyncio.sleep(duration)
    return f"{name} completed in {duration} seconds"

# ==================================================
# 11. HEALTH CHECK AND MONITORING
# ==================================================

@app.get("/health")
async def health_check():
    """
    Health check endpoint with background task statistics
    """
    task_stats = {
        "total": len(task_storage),
        "pending": sum(1 for task in task_storage.values() if task.status == "pending"),
        "running": sum(1 for task in task_storage.values() if task.status == "running"),
        "completed": sum(1 for task in task_storage.values() if task.status == "completed"),
        "failed": sum(1 for task in task_storage.values() if task.status == "failed")
    }
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "task_statistics": task_stats,
        "scheduler_active": True
    }

"""
How to Run This Example:
1. Save this file as 12_background_tasks.py
2. Install dependencies: pip install fastapi uvicorn aiofiles
3. Run: uvicorn 12_background_tasks:app --reload
4. Test endpoints:
   - POST /send-email (with email data)
   - POST /process-file (with file processing request)
   - POST /generate-report (with report parameters)
   - GET /task-status/{task_id} (check task progress)
   - GET /tasks (list all tasks)
   - GET /health (system health with task stats)

Example requests:
curl -X POST "http://127.0.0.1:8000/send-email" \
  -H "Content-Type: application/json" \
  -d '{"to": "user@example.com", "subject": "Test", "body": "Hello!"}'

curl -X POST "http://127.0.0.1:8000/process-file" \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/path/to/image.jpg", "operation": "resize", "parameters": {"width": 800, "height": 600}}'

Key Learning Points:
1. Background tasks don't block response to user
2. Use BackgroundTasks for simple operations
3. Implement task tracking for long-running operations
4. Handle errors gracefully in background tasks
5. Monitor task progress and system health
6. Use async/await for I/O-bound operations
7. Schedule periodic tasks for maintenance
8. Consider using Redis/Celery for production task queues
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 