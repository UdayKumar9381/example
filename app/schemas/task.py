from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List
from enum import Enum


class TaskTypeEnum(str, Enum):
    STORY = "STORY"
    TASK = "TASK"
    BUG = "BUG"
    EPIC = "EPIC"
    SUBTASK = "SUBTASK"


class TaskStatusEnum(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    ARCHIVED = "ARCHIVED"


class TaskPriorityEnum(str, Enum):
    LOWEST = "LOWEST"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    HIGHEST = "HIGHEST"


# ----------------------------
# CREATE / UPDATE
# ----------------------------

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    task_type: TaskTypeEnum = TaskTypeEnum.TASK
    priority: TaskPriorityEnum = TaskPriorityEnum.MEDIUM
    story_points: Optional[int] = Field(None, ge=0, le=100)
    assignee_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    due_date: Optional[date] = None
    start_date: Optional[date] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    task_type: Optional[TaskTypeEnum] = None
    priority: Optional[TaskPriorityEnum] = None
    story_points: Optional[int] = Field(None, ge=0, le=100)
    assignee_id: Optional[str] = None
    due_date: Optional[date] = None
    start_date: Optional[date] = None


# ----------------------------
# STATUS / POSITION
# ----------------------------

class TaskStatusUpdate(BaseModel):
    status: TaskStatusEnum


class TaskPositionUpdate(BaseModel):
    status: TaskStatusEnum
    position: int = Field(..., ge=0)


# ----------------------------
# ✅ FIX: ASSIGNEE UPDATE (REQUIRED)
# ----------------------------

class TaskAssigneeUpdate(BaseModel):
    assignee_ids: List[int]


# ----------------------------
# ATTACHMENTS
# ----------------------------

class TaskAttachmentResponse(BaseModel):
    id: str
    filename: str
    file_size: int
    mime_type: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ----------------------------
# RESPONSES
# ----------------------------

class TaskResponse(BaseModel):
    id: str
    project_id: str
    task_key: str
    task_number: int
    title: str
    description: Optional[str]
    task_type: str
    status: str
    priority: str
    story_points: Optional[int]
    parent_task_id: Optional[str]
    assignee_id: Optional[str]
    assignee_name: Optional[str] = None
    reporter_id: str
    reporter_name: Optional[str] = None
    due_date: Optional[date]
    start_date: Optional[date]
    position: int
    created_at: datetime
    updated_at: datetime
    subtask_count: int = 0
    attachment_count: int = 0

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int


# ----------------------------
# KANBAN BOARD
# ----------------------------

class BoardColumn(BaseModel):
    status: str
    tasks: List[TaskResponse]
    count: int


class BoardResponse(BaseModel):
    project_id: str
    project_key: str
    columns: List[BoardColumn]
