from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import uuid4
from datetime import datetime, timedelta

from app.models.activity import Activity, ActionType


def create_activity(
    db: Session,
    project_id: str,
    user_id: str,
    action: ActionType,
    task_id: str = None,
    task_key: str = None,
    old_value: str = None,
    new_value: str = None,
    metadata: dict = None
) -> Activity:
    activity = Activity(
        id=str(uuid4()),
        project_id=project_id,
        task_id=task_id,
        user_id=user_id,
        action=action,
        task_key=task_key,
        old_value=old_value,
        new_value=new_value,
        metadata=metadata
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def get_project_activities(db: Session, project_id: str, skip: int = 0, limit: int = 50) -> list[Activity]:
    return db.query(Activity).filter(
        Activity.project_id == project_id
    ).order_by(Activity.created_at.desc()).offset(skip).limit(limit).all()


def get_task_activities(db: Session, task_id: str) -> list[Activity]:
    return db.query(Activity).filter(
        Activity.task_id == task_id
    ).order_by(Activity.created_at.desc()).all()


def get_user_activities(db: Session, user_id: str, limit: int = 50) -> list[Activity]:
    return db.query(Activity).filter(
        Activity.user_id == user_id
    ).order_by(Activity.created_at.desc()).limit(limit).all()


def get_recent_activities(db: Session, project_ids: list[str], limit: int = 20) -> list[Activity]:
    return db.query(Activity).filter(
        Activity.project_id.in_(project_ids)
    ).order_by(Activity.created_at.desc()).limit(limit).all()


def get_activity_stats(db: Session, project_id: str, days: int = 7) -> dict:
    start_date = datetime.utcnow() - timedelta(days=days)
    
    activities = db.query(
        Activity.action,
        func.count(Activity.id).label("count")
    ).filter(
        Activity.project_id == project_id,
        Activity.created_at >= start_date
    ).group_by(Activity.action).all()
    
    return {activity.action.value: activity.count for activity in activities}