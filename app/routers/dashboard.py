from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.task import Task, TaskStatus
from app.models.activity import Activity
from app.crud import project as project_crud
from app.crud import activity as activity_crud

router = APIRouter()


class StatusCount(BaseModel):
    status: str
    count: int


class DashboardSummary(BaseModel):
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    todo_tasks: int
    total_projects: int


class ActivityItem(BaseModel):
    id: str
    action: str
    task_key: str | None
    user_name: str
    created_at: datetime


class DashboardResponse(BaseModel):
    summary: DashboardSummary
    status_overview: List[StatusCount]
    recent_activities: List[ActivityItem]


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    request: Request,
    db: Session = Depends(get_db)
):
    user_id = request.state.user_id
    
    projects = project_crud.get_user_projects(db, user_id)
    project_ids = [p.id for p in projects]
    
    if not project_ids:
        return DashboardResponse(
            summary=DashboardSummary(
                total_tasks=0,
                completed_tasks=0,
                in_progress_tasks=0,
                todo_tasks=0,
                total_projects=0
            ),
            status_overview=[],
            recent_activities=[]
        )
    
    status_counts = db.query(
        Task.status,
        func.count(Task.id).label("count")
    ).filter(
        Task.project_id.in_(project_ids)
    ).group_by(Task.status).all()
    
    status_map = {sc.status.value: sc.count for sc in status_counts}
    
    total_tasks = sum(status_map.values())
    completed = status_map.get(TaskStatus.DONE.value, 0)
    in_progress = status_map.get(TaskStatus.IN_PROGRESS.value, 0)
    todo = status_map.get(TaskStatus.TODO.value, 0)
    
    activities = activity_crud.get_recent_activities(db, project_ids, limit=10)
    
    return DashboardResponse(
        summary=DashboardSummary(
            total_tasks=total_tasks,
            completed_tasks=completed,
            in_progress_tasks=in_progress,
            todo_tasks=todo,
            total_projects=len(projects)
        ),
        status_overview=[
            StatusCount(status=status, count=count)
            for status, count in status_map.items()
        ],
        recent_activities=[
            ActivityItem(
                id=act.id,
                action=act.action.value,
                task_key=act.task_key,
                user_name=act.user.display_name,
                created_at=act.created_at
            )
            for act in activities
        ]
    )


@router.get("/my-tasks")
async def get_my_tasks(
    request: Request,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    from app.crud import task as task_crud
    
    tasks = task_crud.get_user_assigned_tasks(db, request.state.user_id, limit)
    
    return {
        "tasks": [
            {
                "id": task.id,
                "task_key": task.task_key,
                "title": task.title,
                "status": task.status.value,
                "priority": task.priority.value,
                "project_key": task.project.project_key,
                "due_date": task.due_date
            }
            for task in tasks
        ]
    }


@router.get("/activity-stats")
async def get_activity_stats(
    request: Request,
    days: int = 7,
    db: Session = Depends(get_db)
):
    user_id = request.state.user_id
    projects = project_crud.get_user_projects(db, user_id)
    
    all_stats = {}
    for project in projects:
        stats = activity_crud.get_activity_stats(db, project.id, days)
        for action, count in stats.items():
            all_stats[action] = all_stats.get(action, 0) + count
    
    return {"stats": all_stats, "days": days}