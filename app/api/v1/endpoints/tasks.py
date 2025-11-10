from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.domain import TaskCreate, TaskUpdate, TaskResponse
from app.models.database import get_db
from app.repositories.task_repository import SQLAlchemyTaskRepository
from app.services.task_service import TaskService
from app.models.enums import TaskStatus, TaskPriority

router = APIRouter()


def get_service(db: Session = Depends(get_db)) -> TaskService:
    repo = SQLAlchemyTaskRepository(db)
    return TaskService(repo)


@router.post("/tasks", response_model=TaskResponse, status_code=201)
def create_task(task: TaskCreate, service: TaskService = Depends(get_service)):
    created = service.create_task(task)
    return created


@router.get("/tasks", response_model=List[TaskResponse])
def get_tasks(
    status: Optional[TaskStatus] = Query(None),
    priority: Optional[TaskPriority] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: TaskService = Depends(get_service)
):
    return service.list_tasks(status, priority, skip, limit)


@router.get("/tasks/export/csv")
def export_tasks_csv(service: TaskService = Depends(get_service)):
    tasks = service.export_all()
    # Build CSV streaming here to avoid SQL in routes
    import io, csv
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['id', 'title', 'description', 'status', 'priority', 'created_at', 'updated_at'])
    for t in tasks:
        writer.writerow([t.id, t.title, t.description, t.status, t.priority, t.created_at.isoformat(), t.updated_at.isoformat()])
    output.seek(0)
    from fastapi.responses import StreamingResponse
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=tasks.csv"})


@router.get("/tasks/stats")
def get_task_stats(service: TaskService = Depends(get_service)):
    return service.stats()


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, service: TaskService = Depends(get_service)):
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task_update: TaskUpdate, service: TaskService = Depends(get_service)):
    updated = service.update_task(task_id, task_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, service: TaskService = Depends(get_service)):
    ok = service.delete_task(task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")
    return None
