from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app.database import get_db
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    TaskStatusUpdate,
    TaskPositionUpdate,
    TaskAttachmentResponse,
    BoardResponse,
    BoardColumn
)
from app.crud import task as task_crud
from app.crud import project as project_crud
from app.crud import activity as activity_crud
from app.models.activity import ActionType
from app.permissions.access_control import require_project_access, ProjectPermission
from app.services.file_service import FileService

router = APIRouter()


def build_task_response(task) -> TaskResponse:
    return TaskResponse(
        id=task.id,
        project_id=task.project_id,
        task_key=task.task_key,
        task_number=task.task_number,
        title=task.title,
        description=task.description,
        task_type=task.task_type.value,
        status=task.status.value,
        priority=task.priority.value,
        story_points=task.story_points,
        parent_task_id=task.parent_task_id,
        assignee_id=task.assignee_id,
        assignee_name=task.assignee.display_name if task.assignee else None,
        reporter_id=task.reporter_id,
        reporter_name=task.reporter.display_name if task.reporter else None,
        due_date=task.due_date,
        start_date=task.start_date,
        position=task.position,
        created_at=task.created_at,
        updated_at=task.updated_at,
        subtask_count=len(task.subtasks) if hasattr(task, 'subtasks') else 0,
        attachment_count=len(task.attachments) if hasattr(task, 'attachments') else 0
    )


@router.get("/project/{project_id}", response_model=TaskListResponse)
async def list_project_tasks(
    request: Request,
    project_id: str,
    status: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    require_project_access(db, project_id, request.state.user_id, ProjectPermission.VIEW)
    
    tasks = task_crud.get_project_tasks(db, project_id, status, skip, limit)
    
    return TaskListResponse(
        tasks=[build_task_response(task) for task in tasks],
        total=len(tasks)
    )


@router.get("/project/{project_id}/board", response_model=BoardResponse)
async def get_project_board(
    request: Request,
    project_id: str,
    db: Session = Depends(get_db)
):
    require_project_access(db, project_id, request.state.user_id, ProjectPermission.VIEW)
    
    project = project_crud.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    board = task_crud.get_board_tasks(db, project_id)
    
    columns = [
        BoardColumn(
            status=status_name,
            tasks=[build_task_response(task) for task in tasks],
            count=len(tasks)
        )
        for status_name, tasks in board.items()
    ]
    
    return BoardResponse(
        project_id=project_id,
        project_key=project.project_key,
        columns=columns
    )


@router.post("/project/{project_id}", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    request: Request,
    project_id: str,
    task_data: TaskCreate,
    db: Session = Depends(get_db)
):
    require_project_access(db, project_id, request.state.user_id, ProjectPermission.EDIT)
    
    task = task_crud.create_task(db, project_id, task_data, request.state.user_id)
    
    activity_crud.create_activity(
        db,
        project_id=project_id,
        task_id=task.id,
        user_id=request.state.user_id,
        action=ActionType.TASK_CREATED,
        task_key=task.task_key
    )
    
    return build_task_response(task)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    request: Request,
    task_id: str,
    db: Session = Depends(get_db)
):
    task = task_crud.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    require_project_access(db, task.project_id, request.state.user_id, ProjectPermission.VIEW)
    
    return build_task_response(task)


@router.get("/key/{task_key}", response_model=TaskResponse)
async def get_task_by_key(
    request: Request,
    task_key: str,
    db: Session = Depends(get_db)
):
    task = task_crud.get_task_by_key(db, task_key)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    require_project_access(db, task.project_id, request.state.user_id, ProjectPermission.VIEW)
    
    return build_task_response(task)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    request: Request,
    task_id: str,
    update_data: TaskUpdate,
    db: Session = Depends(get_db)
):
    task = task_crud.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    require_project_access(db, task.project_id, request.state.user_id, ProjectPermission.EDIT)
    
    old_assignee = task.assignee_id
    updated_task = task_crud.update_task(db, task_id, update_data)
    
    activity_crud.create_activity(
        db,
        project_id=task.project_id,
        task_id=task_id,
        user_id=request.state.user_id,
        action=ActionType.TASK_UPDATED,
        task_key=task.task_key
    )
    
    if update_data.assignee_id and update_data.assignee_id != old_assignee:
        activity_crud.create_activity(
            db,
            project_id=task.project_id,
            task_id=task_id,
            user_id=request.state.user_id,
            action=ActionType.ASSIGNEE_CHANGED,
            task_key=task.task_key,
            old_value=old_assignee,
            new_value=update_data.assignee_id
        )
    
    return build_task_response(updated_task)


@router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    request: Request,
    task_id: str,
    status_data: TaskStatusUpdate,
    db: Session = Depends(get_db)
):
    task = task_crud.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    require_project_access(db, task.project_id, request.state.user_id, ProjectPermission.EDIT)
    
    old_status = task.status.value
    updated_task = task_crud.update_task_status(db, task_id, status_data.status)
    
    activity_crud.create_activity(
        db,
        project_id=task.project_id,
        task_id=task_id,
        user_id=request.state.user_id,
        action=ActionType.STATUS_CHANGED,
        task_key=task.task_key,
        old_value=old_status,
        new_value=status_data.status.value
    )
    
    return build_task_response(updated_task)


@router.patch("/{task_id}/position", response_model=TaskResponse)
async def update_task_position(
    request: Request,
    task_id: str,
    position_data: TaskPositionUpdate,
    db: Session = Depends(get_db)
):
    task = task_crud.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    require_project_access(db, task.project_id, request.state.user_id, ProjectPermission.EDIT)
    
    old_status = task.status.value
    updated_task = task_crud.update_task_position(db, task_id, position_data.status, position_data.position)
    
    if old_status != position_data.status.value:
        activity_crud.create_activity(
            db,
            project_id=task.project_id,
            task_id=task_id,
            user_id=request.state.user_id,
            action=ActionType.STATUS_CHANGED,
            task_key=task.task_key,
            old_value=old_status,
            new_value=position_data.status.value
        )
    
    return build_task_response(updated_task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    request: Request,
    task_id: str,
    db: Session = Depends(get_db)
):
    task = task_crud.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    require_project_access(db, task.project_id, request.state.user_id, ProjectPermission.DELETE)
    
    task_crud.delete_task(db, task_id)


@router.get("/{task_id}/subtasks", response_model=List[TaskResponse])
async def get_subtasks(
    request: Request,
    task_id: str,
    db: Session = Depends(get_db)
):
    task = task_crud.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    require_project_access(db, task.project_id, request.state.user_id, ProjectPermission.VIEW)
    
    subtasks = task_crud.get_subtasks(db, task_id)
    return [build_task_response(subtask) for subtask in subtasks]


@router.post("/{task_id}/attachments", response_model=TaskAttachmentResponse)
async def upload_attachment(
    request: Request,
    task_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    task = task_crud.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    require_project_access(db, task.project_id, request.state.user_id, ProjectPermission.EDIT)
    
    file_service = FileService()
    file_info = await file_service.save_file(file, task_id)
    
    attachment = task_crud.create_attachment(
        db,
        task_id=task_id,
        filename=file_info["filename"],
        file_path=file_info["file_path"],
        file_size=file_info["file_size"],
        mime_type=file_info["mime_type"],
        uploaded_by=request.state.user_id
    )
    
    activity_crud.create_activity(
        db,
        project_id=task.project_id,
        task_id=task_id,
        user_id=request.state.user_id,
        action=ActionType.ATTACHMENT_ADDED,
        task_key=task.task_key,
        new_value=file_info["filename"]
    )
    
    return TaskAttachmentResponse(
        id=attachment.id,
        filename=attachment.filename,
        file_size=attachment.file_size,
        mime_type=attachment.mime_type,
        created_at=attachment.created_at
    )


@router.get("/{task_id}/attachments", response_model=List[TaskAttachmentResponse])
async def list_attachments(
    request: Request,
    task_id: str,
    db: Session = Depends(get_db)
):
    task = task_crud.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    require_project_access(db, task.project_id, request.state.user_id, ProjectPermission.VIEW)
    
    attachments = task_crud.get_task_attachments(db, task_id)
    return [
        TaskAttachmentResponse(
            id=att.id,
            filename=att.filename,
            file_size=att.file_size,
            mime_type=att.mime_type,
            created_at=att.created_at
        )
        for att in attachments
    ]


@router.delete("/{task_id}/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    request: Request,
    task_id: str,
    attachment_id: str,
    db: Session = Depends(get_db)
):
    task = task_crud.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    require_project_access(db, task.project_id, request.state.user_id, ProjectPermission.EDIT)
    
    if not task_crud.delete_attachment(db, attachment_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )


@router.get("/project/{project_id}/timeline", response_model=List[TaskResponse])
async def get_timeline(
    request: Request,
    project_id: str,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db)
):
    require_project_access(db, project_id, request.state.user_id, ProjectPermission.VIEW)
    
    tasks = task_crud.get_tasks_for_timeline(db, project_id, start_date, end_date)
    return [build_task_response(task) for task in tasks]


@router.get("/project/{project_id}/calendar", response_model=List[TaskResponse])
async def get_calendar(
    request: Request,
    project_id: str,
    year: int,
    month: int,
    db: Session = Depends(get_db)
):
    require_project_access(db, project_id, request.state.user_id, ProjectPermission.VIEW)
    
    tasks = task_crud.get_tasks_for_calendar(db, project_id, year, month)
    return [build_task_response(task) for task in tasks]


@router.get("/project/{project_id}/archived", response_model=TaskListResponse)
async def get_archived_tasks(
    request: Request,
    project_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    require_project_access(db, project_id, request.state.user_id, ProjectPermission.VIEW)
    
    tasks = task_crud.get_archived_tasks(db, project_id, skip, limit)
    return TaskListResponse(
        tasks=[build_task_response(task) for task in tasks],
        total=len(tasks)
    )