from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.database import get_db
from app.crud import project as project_crud
from app.crud import task as task_crud
from app.crud import user as user_crud

router = APIRouter()


class SearchProjectResult(BaseModel):
    id: str
    name: str
    project_key: str
    project_type: str


class SearchTaskResult(BaseModel):
    id: str
    task_key: str
    title: str
    status: str
    project_key: str


class SearchUserResult(BaseModel):
    id: str
    email: str
    display_name: str


class SearchResponse(BaseModel):
    projects: List[SearchProjectResult]
    tasks: List[SearchTaskResult]
    users: List[SearchUserResult]


@router.get("", response_model=SearchResponse)
async def global_search(
    request: Request,
    q: str = Query(..., min_length=1, max_length=100),
    db: Session = Depends(get_db)
):
    user_id = request.state.user_id
    
    projects = project_crud.search_projects(db, q, user_id, limit=5)
    project_results = [
        SearchProjectResult(
            id=p.id,
            name=p.name,
            project_key=p.project_key,
            project_type=p.project_type.value
        )
        for p in projects
    ]
    
    user_projects = project_crud.get_user_projects(db, user_id)
    project_ids = [p.id for p in user_projects]
    
    tasks = task_crud.search_tasks(db, q, project_ids, limit=10) if project_ids else []
    task_results = [
        SearchTaskResult(
            id=t.id,
            task_key=t.task_key,
            title=t.title,
            status=t.status.value,
            project_key=t.project.project_key
        )
        for t in tasks
    ]
    
    users = user_crud.search_users(db, q, limit=5)
    user_results = [
        SearchUserResult(
            id=u.id,
            email=u.email,
            display_name=u.display_name
        )
        for u in users
    ]
    
    return SearchResponse(
        projects=project_results,
        tasks=task_results,
        users=user_results
    )


@router.get("/projects", response_model=List[SearchProjectResult])
async def search_projects(
    request: Request,
    q: str = Query(..., min_length=1, max_length=100),
    db: Session = Depends(get_db)
):
    projects = project_crud.search_projects(db, q, request.state.user_id, limit=10)
    return [
        SearchProjectResult(
            id=p.id,
            name=p.name,
            project_key=p.project_key,
            project_type=p.project_type.value
        )
        for p in projects
    ]


@router.get("/tasks", response_model=List[SearchTaskResult])
async def search_tasks(
    request: Request,
    q: str = Query(..., min_length=1, max_length=100),
    project_id: str = None,
    db: Session = Depends(get_db)
):
    if project_id:
        project_ids = [project_id]
    else:
        user_projects = project_crud.get_user_projects(db, request.state.user_id)
        project_ids = [p.id for p in user_projects]
    
    if not project_ids:
        return []
    
    tasks = task_crud.search_tasks(db, q, project_ids, limit=20)
    return [
        SearchTaskResult(
            id=t.id,
            task_key=t.task_key,
            title=t.title,
            status=t.status.value,
            project_key=t.project.project_key
        )
        for t in tasks
    ]


@router.get("/users", response_model=List[SearchUserResult])
async def search_users(
    request: Request,
    q: str = Query(..., min_length=1, max_length=100),
    db: Session = Depends(get_db)
):
    users = user_crud.search_users(db, q, limit=10)
    return [
        SearchUserResult(
            id=u.id,
            email=u.email,
            display_name=u.display_name
        )
        for u in users
    ]