from sqlalchemy import Column, String, Text, Boolean, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class ProjectType(str, enum.Enum):
    TEAM_MANAGED = "TEAM_MANAGED"
    COMPANY_MANAGED = "COMPANY_MANAGED"


class BoardType(str, enum.Enum):
    KANBAN = "KANBAN"


class MemberRole(str, enum.Enum):
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
    VIEWER = "VIEWER"


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    project_key = Column(String(10), unique=True, nullable=False, index=True)
    description = Column(Text)
    project_type = Column(Enum(ProjectType), nullable=False)
    board_type = Column(Enum(BoardType), default=BoardType.KANBAN)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    owner = relationship("User", back_populates="owned_projects")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="project", cascade="all, delete-orphan")
    labels = relationship("TaskLabel", back_populates="project", cascade="all, delete-orphan")


class ProjectMember(Base):
    __tablename__ = "project_members"
    
    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    role = Column(Enum(MemberRole), default=MemberRole.MEMBER)
    created_at = Column(DateTime, server_default=func.now())
    
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_memberships")