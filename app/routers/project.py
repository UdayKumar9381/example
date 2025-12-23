from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.project import (
    ProjectCreate, 
    ProjectUpdate, 
    ProjectResponse, 
    ProjectListResponse,
    ProjectMemberAdd,
    ProjectMemberResponse
)
from app.crud import project as project_crud
from app.crud import activity as activity_crud
from app.models.activity import ActionType
from app.permissions.access_control import require_role, require_project_access, ProjectPermission

router = APIRouter()


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    user_id = request.state.user_id
    projects = project_crud.get_user_projects(db, user_id, skip, limit)
    total = project_crud.get_project_count(db, user_id)
    
    project_responses = []
    for project in projects:
        stats = project_crud.get_project_stats(db, project.id)
        project_responses.append(ProjectResponse(
            id=project.id,
            name=project.name,
            project_key=project.project_key,
            description=project.description,
            project_type=project.project_type.value,
            board_type=project.board_type.value,
            owner_id=project.owner_id,
            is_archived=project.is_archived,
            created_at=project.created_at,
            updated_at=project.updated_at,
            member_count=stats["member_count"],
            task_count=stats["task_count"]
        ))
    
    return ProjectListResponse(
        projects=project_responses,
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: Request,
    project_data: ProjectCreate,
    db: Session = Depends(get_db)
):
    require_role(request.state.user_role, ["ADMIN", "USER"])
    
    existing = project_crud.get_project_by_key(db, project_data.project_key)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project key already exists"
        )
    
    project = project_crud.create_project(db, project_data, request.state.user_id)
    
    activity_crud.create_activity(
        db,
        project_id=project.id,
        user_id=request.state.user_id,
        action=ActionType.PROJECT_CREATED,
        metadata={"project_name": project.name}
    )
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        project_key=project.project_key,
        description=project.description,
        project_type=project.project_type.value,
        board_type=project.board_type.value,
        owner_id=project.owner_id,
        is_archived=project.is_archived,
        created_at=project.created_at,
        updated_at=project.updated_at
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
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
    
    stats = project_crud.get_project_stats(db, project_id)
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        project_key=project.project_key,
        description=project.description,
        project_type=project.project_type.value,
        board_type=project.board_type.value,
        owner_id=project.owner_id,
        is_archived=project.is_archived,
        created_at=project.created_at,
        updated_at=project.updated_at,
        member_count=stats["member_count"],
        task_count=stats["task_count"]
    )


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    request: Request,
    project_id: str,
    update_data: ProjectUpdate,
    db: Session = Depends(get_db)
):
    require_project_access(db, project_id, request.state.user_id, ProjectPermission.EDIT)
    
    project = project_crud.update_project(db, project_id, update_data)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        project_key=project.project_key,
        description=project.description,
        project_type=project.project_type.value,
        board_type=project.board_type.value,
        owner_id=project.owner_id,
        is_archived=project.is_archived,
        created_at=project.created_at,
        updated_at=project.updated_at
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    request: Request,
    project_id: str,
    db: Session = Depends(get_db)
):
    require_project_access(db, project_id, request.state.user_id, ProjectPermission.DELETE)
    
    if not project_crud.delete_project(db, project_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )


@router.post("/{project_id}/archive", response_model=ProjectResponse)
async def archive_project(
    request: Request,
    project_id: str,
    db: Session = Depends(get_db)
):
    require_project_access(db, project_id, request.state.user_id, ProjectPermission.DELETE)
    
    project = project_crud.archive_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        project_key=project.project_key,
        description=project.description,
        project_type=project.project_type.value,
        board_type=project.board_type.value,
        owner_id=project.owner_id,
        is_archived=project.is_archived,
        created_at=project.created_at,
        updated_at=project.updated_at
    )


@router.get("/{project_id}/members", response_model=List[ProjectMemberResponse])
async def list_project_members(
    request: Request,
    project_id: str,
    db: Session = Depends(get_db)
):
    require_project_access(db, project_id, request.state.user_id, ProjectPermission.VIEW)
    
    members = project_crud.get_project_members(db, project_id)
    
    return [
        ProjectMemberResponse(
            id=member.id,
            user_id=member.user_id,
            display_name=member.user.display_name,
            email=member.user.email,
            role=member.role.value,
            created_at=member.created_at
        )
        for member in members
    ]


@router.post("/{project_id}/members", response_model=ProjectMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_project_member(
    request: Request,
    project_id: str,
    member_data: ProjectMemberAdd,
    db: Session = Depends(get_db)
):
    require_project_access(db, project_id, request.state.user_id, ProjectPermission.MANAGE_MEMBERS)
    
    existing = project_crud.get_project_member(db, project_id, member_data.user_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member"
        )
    
    member = project_crud.add_project_member(db, project_id, member_data)
    
    activity_crud.create_activity(
        db,
        project_id=project_id,
        user_id=request.state.user_id,
        action=ActionType.MEMBER_ADDED,
        new_value=member_data.user_id
    )
    
    return ProjectMemberResponse(
        id=member.id,
        user_id=member.user_id,
        display_name=member.user.display_name,
        email=member.user.email,
        role=member.role.value,
        created_at=member.created_at
    )


@router.delete("/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_project_member(
    request: Request,
    project_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    require_project_access(db, project_id, request.state.user_id, ProjectPermission.MANAGE_MEMBERS)
    
    if not project_crud.remove_project_member(db, project_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    activity_crud.create_activity(
        db,
        project_id=project_id,
        user_id=request.state.user_id,
        action=ActionType.MEMBER_REMOVED,
        old_value=user_id
    )