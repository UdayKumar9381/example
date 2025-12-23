from sqlalchemy import Column, String, Enum, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class ActionType(str, enum.Enum):
    TASK_CREATED = "TASK_CREATED"
    TASK_UPDATED = "TASK_UPDATED"
    STATUS_CHANGED = "STATUS_CHANGED"
    ASSIGNEE_CHANGED = "ASSIGNEE_CHANGED"
    COMMENT_ADDED = "COMMENT_ADDED"
    ATTACHMENT_ADDED = "ATTACHMENT_ADDED"
    PROJECT_CREATED = "PROJECT_CREATED"
    MEMBER_ADDED = "MEMBER_ADDED"
    MEMBER_REMOVED = "MEMBER_REMOVED"


class Activity(Base):
    __tablename__ = "activities"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    action = Column(Enum(ActionType), nullable=False)
    task_key = Column(String(20))
    old_value = Column(String(255))
    new_value = Column(String(255))

    # 🔥 FIXED: renamed from `metadata`
    extra_data = Column(JSON)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="activities")
    task = relationship("Task", back_populates="activities")
    user = relationship("User", back_populates="activities")
