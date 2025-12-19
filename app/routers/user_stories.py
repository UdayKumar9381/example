# app/routers/user_stories.py
"""
API endpoints for User Story operations.
Handles all HTTP requests related to user stories.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app import crud
from app.schemas import (
    UserStoryCreateResponse,
    UserStoryDetailResponse,
    StoryStatusEnum,
    ErrorResponse
)
from app.file_handler import save_upload_file, format_file_size

# Create router with prefix and tags
router = APIRouter(
    prefix="/api/v1/user-stories",
    tags=["User Stories"],
    responses={
        404: {"model": ErrorResponse, "description": "Story not found"},
        400: {"model": ErrorResponse, "description": "Bad request"}
    }
)


@router.post(
    "/",
    response_model=UserStoryCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new User Story",
    description="""
    Create a new user story with all required fields and a support document.
    
    **Important Notes:**
    - Support document (file upload) is MANDATORY
    - If a file with the same name exists, it will be overwritten
    - The response includes an `override` flag indicating if a file was replaced
    """
)
async def create_user_story(
    # Form fields for story data
    project_name: str = Form(
        ..., 
        description="Name of the project",
        min_length=1,
        max_length=255
    ),
    release_number: str = Form(
        ..., 
        description="Release version (e.g., 'v2.1.0')",
        min_length=1,
        max_length=50
    ),
    sprint_number: str = Form(
        ..., 
        description="Sprint identifier (e.g., 'Sprint 15')",
        min_length=1,
        max_length=50
    ),
    story_pointer: int = Form(
        ..., 
        description="Story points (1-21)",
        ge=1,
        le=21
    ),
    assignee: str = Form(
        ..., 
        description="Person assigned to the story",
        min_length=1,
        max_length=255
    ),
    reviewer: str = Form(
        ..., 
        description="Person reviewing the story",
        min_length=1,
        max_length=255
    ),
    title: str = Form(
        ..., 
        description="Story title",
        min_length=1,
        max_length=500
    ),
    description: Optional[str] = Form(
        None, 
        description="Detailed description"
    ),
    status: StoryStatusEnum = Form(
        default=StoryStatusEnum.TODO, 
        description="Initial status"
    ),
    # File upload - MANDATORY
    support_document: UploadFile = File(
        ..., 
        description="Support document file (MANDATORY)"
    ),
    # Database session dependency
    db: Session = Depends(get_db)
):
    """
    Create a new user story endpoint.
    
    This endpoint:
    1. Validates all form fields
    2. Saves the uploaded file to the uploads directory
    3. Creates a database record with story details and file metadata
    4. Returns the complete story with override flag
    """
    
    # Step 1: Save the uploaded file
    # This handles validation, saving, and override detection
    file_name, file_path, file_size, was_overridden = await save_upload_file(
        support_document
    )
    
    # Step 2: Prepare story data for database
    story_data = {
        "project_name": project_name,
        "release_number": release_number,
        "sprint_number": sprint_number,
        "story_pointer": story_pointer,
        "assignee": assignee,
        "reviewer": reviewer,
        "title": title,
        "description": description,
        "status": status.value  # Convert enum to string for database
    }
    
    # Step 3: Create story in database
    db_story = crud.create_user_story(
        db=db,
        story_data=story_data,
        file_name=file_name,
        file_path=file_path,
        file_size_bytes=file_size
    )
    
    # Step 4: Build response with all required fields
    return UserStoryCreateResponse(
        id=db_story.id,
        project_name=db_story.project_name,
        release_number=db_story.release_number,
        sprint_number=db_story.sprint_number,
        story_pointer=db_story.story_pointer,
        assignee=db_story.assignee,
        reviewer=db_story.reviewer,
        title=db_story.title,
        description=db_story.description,
        status=db_story.status,
        file_name=db_story.file_name,
        file_path=db_story.file_path,
        file_size_bytes=db_story.file_size_bytes,
        file_size_formatted=format_file_size(db_story.file_size_bytes),
        created_at=db_story.created_at,
        updated_at=db_story.updated_at,
        override=was_overridden,
        message="User story created successfully" + (
            " (file was overwritten)" if was_overridden else ""
        )
    )


@router.get(
    "/{story_id}",
    response_model=UserStoryDetailResponse,
    summary="Get a User Story by ID",
    description="Retrieve a single user story with all its details and file information."
)
def get_user_story(
    story_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific user story by its ID.
    
    Returns all story fields including file metadata.
    """
    # Fetch story from database
    db_story = crud.get_user_story_by_id(db, story_id)
    
    # Handle not found
    if not db_story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User story with ID {story_id} not found"
        )
    
    # Build response with formatted file size
    return UserStoryDetailResponse(
        id=db_story.id,
        project_name=db_story.project_name,
        release_number=db_story.release_number,
        sprint_number=db_story.sprint_number,
        story_pointer=db_story.story_pointer,
        assignee=db_story.assignee,
        reviewer=db_story.reviewer,
        title=db_story.title,
        description=db_story.description,
        status=db_story.status,
        file_name=db_story.file_name,
        file_path=db_story.file_path,
        file_size_bytes=db_story.file_size_bytes,
        file_size_formatted=format_file_size(db_story.file_size_bytes),
        created_at=db_story.created_at,
        updated_at=db_story.updated_at
    )


@router.get(
    "/",
    response_model=List[UserStoryDetailResponse],
    summary="Get all User Stories",
    description="Retrieve all user stories with pagination support."
)
def get_all_user_stories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve all user stories with optional pagination.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
    """
    stories = crud.get_all_user_stories(db, skip=skip, limit=limit)
    
    return [
        UserStoryDetailResponse(
            id=story.id,
            project_name=story.project_name,
            release_number=story.release_number,
            sprint_number=story.sprint_number,
            story_pointer=story.story_pointer,
            assignee=story.assignee,
            reviewer=story.reviewer,
            title=story.title,
            description=story.description,
            status=story.status,
            file_name=story.file_name,
            file_path=story.file_path,
            file_size_bytes=story.file_size_bytes,
            file_size_formatted=format_file_size(story.file_size_bytes),
            created_at=story.created_at,
            updated_at=story.updated_at
        )
        for story in stories
    ]