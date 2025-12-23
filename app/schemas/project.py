from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class ProjectTypeEnum(str, Enum):
    TEAM_MANAGED = "TEAM_MANAGED"
    COMPANY_MANAGED = "COMPANY_MANAGED"


class MemberRoleEnum(str, Enum):
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
    VIEWER = "VIEWER"


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    project_key: str = Field(..., min_length=2, max_length=10, pattern="^[A-Z]+$")
    description: Optional[str] = None
    project_type: ProjectTypeEnum


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectMemberAdd(BaseModel):
    user_id: str
    role: MemberRoleEnum = MemberRoleEnum.MEMBER


class ProjectMemberResponse(BaseModel):
    id: str
    user_id: str
    display_name: str
    email: str
    role: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProjectResponse(BaseModel):
    id: str
    name: str
    project_key: str
    description: Optional[str]
    project_type: str
    board_type: str
    owner_id: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    member_count: Optional[int] = 0
    task_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    total: int
    page: int
    per_page: int