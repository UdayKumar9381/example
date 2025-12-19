# app/models.py
"""
SQLAlchemy ORM models representing database tables.
Each model maps to a MySQL table.
"""

from sqlalchemy import Column, Integer, String, Text, Enum, BigInteger, TIMESTAMP
from sqlalchemy.sql import func
from app.database import Base
import enum


class StoryStatus(str, enum.Enum):
    """
    Enumeration for User Story status.
    Using str mixin allows JSON serialization.
    """
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    DONE = "DONE"
    BLOCKED = "BLOCKED"


class UserStory(Base):
    """
    UserStory model representing the user_story table.
    
    This model stores all information about a user story including:
    - Project metadata (project, release, sprint)
    - Story details (title, description, status, pointer)
    - Team assignments (assignee, reviewer)
    - Attached document information (file metadata)
    """
    
    __tablename__ = "user_story"
    
    # Primary Key
    id = Column(
        Integer, 
        primary_key=True, 
        index=True, 
        autoincrement=True,
        comment="Unique identifier for the user story"
    )
    
    # Project Information
    project_name = Column(
        String(255), 
        nullable=False, 
        index=True,
        comment="Name of the project this story belongs to"
    )
    release_number = Column(
        String(50), 
        nullable=False,
        comment="Release version number (e.g., 'v1.0', 'R2024.1')"
    )
    sprint_number = Column(
        String(50), 
        nullable=False, 
        index=True,
        comment="Sprint identifier (e.g., 'Sprint 5', 'S2024-01')"
    )
    
    # Story Details
    story_pointer = Column(
        Integer, 
        nullable=False,
        comment="Story points estimate (e.g., 1, 2, 3, 5, 8)"
    )
    title = Column(
        String(500), 
        nullable=False,
        comment="Brief title of the user story"
    )
    description = Column(
        Text, 
        nullable=True,
        comment="Detailed description of the user story"
    )
    status = Column(
        Enum(StoryStatus), 
        nullable=False, 
        default=StoryStatus.TODO,
        index=True,
        comment="Current status of the story"
    )
    
    # Team Members
    assignee = Column(
        String(255), 
        nullable=False, 
        index=True,
        comment="Person assigned to work on this story"
    )
    reviewer = Column(
        String(255), 
        nullable=False,
        comment="Person responsible for reviewing this story"
    )
    
    # File Metadata (Support Document)
    file_name = Column(
        String(500), 
        nullable=False,
        comment="Original name of the uploaded file"
    )
    file_path = Column(
        String(1000), 
        nullable=False,
        comment="Server path where file is stored"
    )
    file_size_bytes = Column(
        BigInteger, 
        nullable=False,
        comment="File size in bytes"
    )
    
    # Timestamps (auto-managed by database)
    created_at = Column(
        TIMESTAMP, 
        server_default=func.current_timestamp(),
        comment="When the story was created"
    )
    updated_at = Column(
        TIMESTAMP, 
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        comment="When the story was last updated"
    )
    
    def __repr__(self):
        """String representation for debugging."""
        return f"<UserStory(id={self.id}, title='{self.title[:30]}...', status={self.status})>"