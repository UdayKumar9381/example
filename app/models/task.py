from sqlalchemy import Column, String, Text, Integer, Date, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class TaskType(str, enum.Enum):
    STORY = "STORY"
    TASK = "TASK"
    BUG = "BUG"
    EPIC = "EPIC"
    SUBTASK = "SUBTASK"


class TaskStatus(str, enum.Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    ARCHIVED = "ARCHIVED"


class TaskPriority(str, enum.Enum):
    LOWEST = "LOWEST"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    HIGHEST = "HIGHEST"


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    task_key = Column(String(20), unique=True, nullable=False)
    task_number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    task_type = Column(Enum(TaskType), default=TaskType.TASK)
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    story_points = Column(Integer)
    parent_task_id = Column(String(36), ForeignKey("tasks.id"))
    assignee_id = Column(String(36), ForeignKey("users.id"))
    reporter_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    due_date = Column(Date)
    start_date = Column(Date)
    position = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    project = relationship("Project", back_populates="tasks")
    parent_task = relationship("Task", remote_side="Task.id", backref="subtasks")
    assignee = relationship("User", back_populates="assigned_tasks", foreign_keys=[assignee_id])
    reporter = relationship("User", back_populates="reported_tasks", foreign_keys=[reporter_id])
    attachments = relationship("TaskAttachment", back_populates="task", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="task")


class TaskAttachment(Base):
    __tablename__ = "task_attachments"
    
    id = Column(String(36), primary_key=True)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100))
    uploaded_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    task = relationship("Task", back_populates="attachments")


class TaskLabel(Base):
    __tablename__ = "task_labels"
    
    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    name = Column(String(50), nullable=False)
    color = Column(String(7), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    project = relationship("Project", back_populates="labels")