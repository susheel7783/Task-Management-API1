from typing import List, Optional, Protocol, Dict, Any
from sqlalchemy.orm import Session
from app.models.database import TaskDB
from app.models.enums import TaskStatus, TaskPriority
from datetime import datetime, timezone

class ITaskRepository(Protocol):
    def create(self, data: Dict[str, Any]) -> TaskDB: ...
    def list(self, status: Optional[str], priority: Optional[str], skip: int, limit: int) -> List[TaskDB]: ...
    def get(self, task_id: int) -> Optional[TaskDB]: ...
    def update(self, task: TaskDB, fields: Dict[str, Any]) -> TaskDB: ...
    def delete(self, task: TaskDB) -> None: ...
    def all(self) -> List[TaskDB]: ...
    def stats(self) -> Dict[str, Any]: ...

class SQLAlchemyTaskRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data):
        task = TaskDB(**data)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def list(self, status=None, priority=None, skip=0, limit=100):
        q = self.db.query(TaskDB)
        if status:
            q = q.filter(TaskDB.status == status)
        if priority:
            q = q.filter(TaskDB.priority == priority)
        return q.offset(skip).limit(limit).all()

    def get(self, task_id: int):
        return self.db.query(TaskDB).filter(TaskDB.id == task_id).first()

    def update(self, task: TaskDB, fields: Dict[str, Any]):
        for k, v in fields.items():
            setattr(task, k, v)
        task.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(task)
        return task

    def delete(self, task: TaskDB):
        self.db.delete(task)
        self.db.commit()

    def all(self):
        return self.db.query(TaskDB).all()

    def stats(self):
        from sqlalchemy import func
        status_counts = self.db.query(TaskDB.status, func.count(TaskDB.id)).group_by(TaskDB.status).all()
        priority_counts = self.db.query(TaskDB.priority, func.count(TaskDB.id)).group_by(TaskDB.priority).all()
        total = self.db.query(func.count(TaskDB.id)).scalar()
        return {
            "total_tasks": total,
            "by_status": {s: c for s, c in status_counts},
            "by_priority": {p: c for p, c in priority_counts}
        }
