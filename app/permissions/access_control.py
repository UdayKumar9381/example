from enum import Enum
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectMember, MemberRole, ProjectType
from app.models.user import UserRole


class ProjectPermission(str, Enum):
    VIEW = "VIEW"
    EDIT = "EDIT"
    DELETE = "DELETE"
    MANAGE_MEMBERS = "MANAGE_MEMBERS"


ROLE_PERMISSIONS = {
    MemberRole.ADMIN: [ProjectPermission.VIEW, ProjectPermission.EDIT, ProjectPermission.DELETE, ProjectPermission.MANAGE_MEMBERS],
    MemberRole.MEMBER: [ProjectPermission.VIEW, ProjectPermission.EDIT],
    MemberRole.VIEWER: [ProjectPermission.VIEW]
}

GLOBAL_ROLE_OVERRIDE = {
    UserRole.ADMIN: [ProjectPermission.VIEW, ProjectPermission.EDIT, ProjectPermission.DELETE, ProjectPermission.MANAGE_MEMBERS],
    UserRole.USER: [],
    UserRole.VIEWER: [ProjectPermission.VIEW]
}


def require_role(user_role: str, allowed_roles: list[str]):
    if user_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )


def require_project_access(
    db: Session,
    project_id: str,
    user_id: str,
    permission: ProjectPermission
):
    from app.crud.user import get_user_by_id
    
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if user.role == UserRole.ADMIN:
        return True
    
    if user.role == UserRole.VIEWER and permission != ProjectPermission.VIEW:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Viewers can only view content"
        )
    
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this project"
        )
    
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if project.project_type == ProjectType.COMPANY_MANAGED:
        if member.role == MemberRole.VIEWER and permission != ProjectPermission.VIEW:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions in company-managed project"
            )
        if member.role == MemberRole.MEMBER and permission in [ProjectPermission.DELETE, ProjectPermission.MANAGE_MEMBERS]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can perform this action in company-managed projects"
            )
    
    allowed_permissions = ROLE_PERMISSIONS.get(member.role, [])
    if permission not in allowed_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    return True


def check_task_access(db: Session, task_id: str, user_id: str, permission: ProjectPermission):
    from app.crud.task import get_task_by_id
    
    task = get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return require_project_access(db, task.project_id, user_id, permission)