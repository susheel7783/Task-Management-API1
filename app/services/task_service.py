from app.repositories.task_repository import ITaskRepository
from app.models.domain import TaskCreate, TaskUpdate
from typing import Optional, List
from app.models.enums import TaskStatus, TaskPriority

class TaskService:
    def __init__(self, repository: ITaskRepository):
        self.repo = repository

    def create_task(self, payload: TaskCreate):
        data = payload.model_dump()
        return self.repo.create(data)

    def list_tasks(self, status: Optional[TaskStatus], priority: Optional[TaskPriority], skip: int = 0, limit: int = 100):
        status_val = status.value if status else None
        priority_val = priority.value if priority else None
        return self.repo.list(status_val, priority_val, skip, limit)

    def get_task(self, task_id: int):
        return self.repo.get(task_id)

    def update_task(self, task_id: int, payload: TaskUpdate):
        task = self.repo.get(task_id)
        if not task:
            return None
        fields = {k: v for k, v in payload.model_dump(exclude_unset=True).items()}
        return self.repo.update(task, fields)

    def delete_task(self, task_id: int):
        task = self.repo.get(task_id)
        if not task:
            return False
        self.repo.delete(task)
        return True

    def export_all(self):
        return self.repo.all()

    def stats(self):
        return self.repo.stats()
