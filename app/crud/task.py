from sqlalchemy.orm import Session
from sqlalchemy import or_, func, and_
from uuid import uuid4
from datetime import date

from app.models.task import Task, TaskAttachment
from app.models.project import Project
from app.schemas.task import TaskCreate, TaskUpdate, TaskStatusEnum


def get_task_by_id(db: Session, task_id: str) -> Task | None:
    return db.query(Task).filter(Task.id == task_id).first()


def get_task_by_key(db: Session, task_key: str) -> Task | None:
    return db.query(Task).filter(Task.task_key == task_key).first()


def get_project_tasks(db: Session, project_id: str, status: str = None, skip: int = 0, limit: int = 100) -> list[Task]:
    query = db.query(Task).filter(Task.project_id == project_id)
    
    if status:
        query = query.filter(Task.status == status)
    
    return query.order_by(Task.position).offset(skip).limit(limit).all()


def get_next_task_number(db: Session, project_id: str) -> int:
    max_number = db.query(func.max(Task.task_number)).filter(Task.project_id == project_id).scalar()
    return (max_number or 0) + 1


def create_task(db: Session, project_id: str, task_data: TaskCreate, reporter_id: str) -> Task:
    project = db.query(Project).filter(Project.id == project_id).first()
    task_number = get_next_task_number(db, project_id)
    task_key = f"{project.project_key}-{task_number}"
    
    max_position = db.query(func.max(Task.position)).filter(
        Task.project_id == project_id,
        Task.status == TaskStatusEnum.TODO
    ).scalar() or 0
    
    task = Task(
        id=str(uuid4()),
        project_id=project_id,
        task_key=task_key,
        task_number=task_number,
        title=task_data.title,
        description=task_data.description,
        task_type=task_data.task_type,
        priority=task_data.priority,
        story_points=task_data.story_points,
        assignee_id=task_data.assignee_id,
        parent_task_id=task_data.parent_task_id,
        reporter_id=reporter_id,
        due_date=task_data.due_date,
        start_date=task_data.start_date,
        position=max_position + 1
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, task_id: str, update_data: TaskUpdate) -> Task | None:
    task = get_task_by_id(db, task_id)
    if not task:
        return None
    
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(task, key, value)
    
    db.commit()
    db.refresh(task)
    return task


def update_task_status(db: Session, task_id: str, status: TaskStatusEnum) -> Task | None:
    task = get_task_by_id(db, task_id)
    if not task:
        return None
    
    old_status = task.status
    task.status = status
    
    max_position = db.query(func.max(Task.position)).filter(
        Task.project_id == task.project_id,
        Task.status == status
    ).scalar() or 0
    task.position = max_position + 1
    
    db.commit()
    db.refresh(task)
    return task


def update_task_position(db: Session, task_id: str, status: TaskStatusEnum, position: int) -> Task | None:
    task = get_task_by_id(db, task_id)
    if not task:
        return None
    
    db.query(Task).filter(
        Task.project_id == task.project_id,
        Task.status == status,
        Task.position >= position,
        Task.id != task_id
    ).update({"position": Task.position + 1})
    
    task.status = status
    task.position = position
    
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task_id: str) -> bool:
    task = get_task_by_id(db, task_id)
    if not task:
        return False
    
    db.delete(task)
    db.commit()
    return True


def get_board_tasks(db: Session, project_id: str) -> dict:
    tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.status != TaskStatusEnum.ARCHIVED
    ).order_by(Task.position).all()
    
    board = {
        TaskStatusEnum.TODO.value: [],
        TaskStatusEnum.IN_PROGRESS.value: [],
        TaskStatusEnum.DONE.value: []
    }
    
    for task in tasks:
        if task.status.value in board:
            board[task.status.value].append(task)
    
    return board


def get_subtasks(db: Session, parent_task_id: str) -> list[Task]:
    return db.query(Task).filter(Task.parent_task_id == parent_task_id).all()


def get_user_assigned_tasks(db: Session, user_id: str, limit: int = 50) -> list[Task]:
    return db.query(Task).filter(
        Task.assignee_id == user_id,
        Task.status != TaskStatusEnum.ARCHIVED
    ).order_by(Task.updated_at.desc()).limit(limit).all()


def create_attachment(db: Session, task_id: str, filename: str, file_path: str, file_size: int, mime_type: str, uploaded_by: str) -> TaskAttachment:
    attachment = TaskAttachment(
        id=str(uuid4()),
        task_id=task_id,
        filename=filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=mime_type,
        uploaded_by=uploaded_by
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


def get_task_attachments(db: Session, task_id: str) -> list[TaskAttachment]:
    return db.query(TaskAttachment).filter(TaskAttachment.task_id == task_id).all()


def delete_attachment(db: Session, attachment_id: str) -> bool:
    attachment = db.query(TaskAttachment).filter(TaskAttachment.id == attachment_id).first()
    if not attachment:
        return False
    
    db.delete(attachment)
    db.commit()
    return True


def search_tasks(db: Session, query: str, project_ids: list[str], limit: int = 20) -> list[Task]:
    return db.query(Task).filter(
        Task.project_id.in_(project_ids),
        or_(
            Task.task_key.ilike(f"%{query}%"),
            Task.title.ilike(f"%{query}%")
        )
    ).limit(limit).all()


def get_tasks_for_timeline(db: Session, project_id: str, start_date: date, end_date: date) -> list[Task]:
    return db.query(Task).filter(
        Task.project_id == project_id,
        Task.status != TaskStatusEnum.ARCHIVED,
        or_(
            and_(Task.start_date >= start_date, Task.start_date <= end_date),
            and_(Task.due_date >= start_date, Task.due_date <= end_date),
            and_(Task.start_date <= start_date, Task.due_date >= end_date)
        )
    ).all()


def get_tasks_for_calendar(db: Session, project_id: str, year: int, month: int) -> list[Task]:
    return db.query(Task).filter(
        Task.project_id == project_id,
        Task.status != TaskStatusEnum.ARCHIVED,
        or_(
            and_(func.year(Task.due_date) == year, func.month(Task.due_date) == month),
            and_(func.year(Task.start_date) == year, func.month(Task.start_date) == month)
        )
    ).all()


def get_archived_tasks(db: Session, project_id: str, skip: int = 0, limit: int = 50) -> list[Task]:
    return db.query(Task).filter(
        Task.project_id == project_id,
        Task.status == TaskStatusEnum.ARCHIVED
    ).offset(skip).limit(limit).all()