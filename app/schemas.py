from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum


class StoryStatusEnum(str, Enum):
    """
    Status options for user stories.
    Matches the database enum.
    """
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    DONE = "DONE"
    BLOCKED = "BLOCKED"


class FileMetadata(BaseModel):
    """
    Schema for file information in responses.
    """
    file_name: str = Field(..., description="Name of the uploaded file")
    file_size_bytes: int = Field(..., description="File size in bytes")
    file_size_formatted: str = Field(..., description="Human-readable file size")
    
    model_config = ConfigDict(from_attributes=True)


class UserStoryBase(BaseModel):
    """
    Base schema with common fields for User Story.
    Inherited by create and response schemas.
    """
    project_name: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        description="Name of the project",
        examples=["E-Commerce Platform"]
    )
    release_number: str = Field(
        ..., 
        min_length=1, 
        max_length=50,
        description="Release version number",
        examples=["v2.1.0"]
    )
    sprint_number: str = Field(
        ..., 
        min_length=1, 
        max_length=50,
        description="Sprint identifier",
        examples=["Sprint 15"]
    )
    story_pointer: int = Field(
        ..., 
        ge=1, 
        le=21,
        description="Story points (Fibonacci: 1,2,3,5,8,13,21)",
        examples=[5]
    )
    assignee: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        description="Person assigned to the story",
        examples=["john.doe@company.com"]
    )
    reviewer: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        description="Person reviewing the story",
        examples=["jane.smith@company.com"]
    )
    title: str = Field(
        ..., 
        min_length=1, 
        max_length=500,
        description="Story title",
        examples=["Implement user authentication"]
    )
    description: Optional[str] = Field(
        None,
        description="Detailed story description",
        examples=["As a user, I want to log in securely..."]
    )
    status: StoryStatusEnum = Field(
        default=StoryStatusEnum.TODO,
        description="Current status of the story"
    )


class UserStoryCreate(UserStoryBase):
    """
    Schema for creating a new user story.
    File is handled separately via Form data.
    Note: File upload is mandatory as per requirements.
    """
    pass


class UserStoryResponse(UserStoryBase):
    """
    Schema for user story responses.
    Includes all base fields plus database-generated fields.
    """
    id: int = Field(..., description="Unique story identifier")
    file_name: str = Field(..., description="Uploaded file name")
    file_path: str = Field(..., description="Server path to file")
    file_size_bytes: int = Field(..., description="File size in bytes")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class UserStoryCreateResponse(UserStoryResponse):
    """
    Response schema specifically for create operations.
    Includes override flag to indicate if file was replaced.
    """
    override: bool = Field(
        ..., 
        description="True if an existing file was overwritten"
    )
    file_size_formatted: str = Field(
        ..., 
        description="Human-readable file size (e.g., '2.5 MB')"
    )
    message: str = Field(
        ..., 
        description="Success message"
    )


class UserStoryDetailResponse(UserStoryResponse):
    """
    Detailed response for single story retrieval.
    Includes formatted file size.
    """
    file_size_formatted: str = Field(
        ..., 
        description="Human-readable file size"
    )


class ErrorResponse(BaseModel):
    """
    Standard error response schema.
    """
    error: bool = True
    message: str
    detail: Optional[str] = None