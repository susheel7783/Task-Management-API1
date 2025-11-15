# Import FastAPI components for building API routes
from fastapi import APIRouter, Depends, HTTPException, Query
# Import type hints for better code documentation and IDE support
from typing import Optional, List
# Import SQLAlchemy's Session for database operations
from sqlalchemy.orm import Session

# Import domain models (Pydantic schemas) for request/response validation
from app.models.domain import TaskCreate, TaskUpdate, TaskResponse
# Import database session factory function
from app.models.database import get_db
# Import the repository layer that handles database queries
from app.repositories.task_repository import SQLAlchemyTaskRepository
# Import the service layer that contains business logic
from app.services.task_service import TaskService
# Import enum types for task status and priority
from app.models.enums import TaskStatus, TaskPriority

# Create an APIRouter instance to organize related endpoints
# This router will be registered with the main FastAPI app
router = APIRouter()


# Dependency injection function that creates a TaskService instance
# This follows the dependency injection pattern to provide services to routes
def get_service(db: Session = Depends(get_db)) -> TaskService:
    # Create a repository instance with the database session
    repo = SQLAlchemyTaskRepository(db)
    # Create and return a service instance with the repository
    # This separates business logic (service) from data access (repository)
    return TaskService(repo)


# POST endpoint to create a new task
# Returns 201 status code (Created) on success
@router.post("/tasks", response_model=TaskResponse, status_code=201)
def create_task(task: TaskCreate, service: TaskService = Depends(get_service)):
    # TaskCreate model validates incoming JSON data
    # The service handles the business logic for creating a task
    created = service.create_task(task)
    # Return the created task (FastAPI auto-converts to JSON using TaskResponse model)
    return created


# GET endpoint to retrieve a list of tasks with optional filtering and pagination
@router.get("/tasks", response_model=List[TaskResponse])
def get_tasks(
    # Optional filter by task status (e.g., "pending", "completed")
    status: Optional[TaskStatus] = Query(None),
    # Optional filter by task priority (e.g., "high", "medium", "low")
    priority: Optional[TaskPriority] = Query(None),
    # Pagination: number of records to skip (must be >= 0)
    skip: int = Query(0, ge=0),
    # Pagination: maximum number of records to return (1-1000)
    limit: int = Query(100, ge=1, le=1000),
    # Inject the service dependency
    service: TaskService = Depends(get_service)
):
    # Delegate to service layer which handles filtering and pagination logic
    return service.list_tasks(status, priority, skip, limit)


# GET endpoint to export all tasks as a CSV file
@router.get("/tasks/export/csv")
def export_tasks_csv(service: TaskService = Depends(get_service)):
    # Retrieve all tasks from the database via service layer
    tasks = service.export_all()
    
    # Import required modules for CSV generation
    import io, csv
    
    # Create an in-memory string buffer to write CSV data
    output = io.StringIO()
    
    # Create a CSV writer that writes to the string buffer
    writer = csv.writer(output)
    
    # Write the CSV header row with column names
    writer.writerow(['id', 'title', 'description', 'status', 'priority', 'created_at', 'updated_at'])
    
    # Iterate through all tasks and write each as a CSV row
    for t in tasks:
        # Convert datetime objects to ISO format strings for CSV compatibility
        writer.writerow([t.id, t.title, t.description, t.status, t.priority, t.created_at.isoformat(), t.updated_at.isoformat()])
    
    # Reset buffer position to the beginning for reading
    output.seek(0)
    
    # Import StreamingResponse for sending files
    from fastapi.responses import StreamingResponse
    
    # Return CSV as a streaming response with appropriate headers
    # Content-Disposition header triggers browser download with filename
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=tasks.csv"})


# GET endpoint to retrieve task statistics
# Returns aggregated data like task counts by status, priority, etc.
@router.get("/tasks/stats")
def get_task_stats(service: TaskService = Depends(get_service)):
    # Delegate to service layer which calculates statistics
    return service.stats()


# GET endpoint to retrieve a single task by its ID
@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, service: TaskService = Depends(get_service)):
    # task_id is extracted from the URL path parameter
    # Fetch the task from the service layer
    task = service.get_task(task_id)
    
    # If task doesn't exist, return 404 error
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Return the found task
    return task


# PUT endpoint to update an existing task
@router.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task_update: TaskUpdate, service: TaskService = Depends(get_service)):
    # task_id from URL path, task_update from request body
    # TaskUpdate model allows partial updates (only changed fields)
    updated = service.update_task(task_id, task_update)
    
    # If task doesn't exist, return 404 error
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Return the updated task
    return updated


# DELETE endpoint to remove a task
# Returns 204 status code (No Content) on successful deletion
@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, service: TaskService = Depends(get_service)):
    # Attempt to delete the task via service layer
    ok = service.delete_task(task_id)
    
    # If task doesn't exist, return 404 error
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Return None (no content in response body for 204 status)
    return None