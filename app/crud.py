# app/crud.py
"""
CRUD (Create, Read, Update, Delete) operations for User Stories.
This module contains all database operations.
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from app.models import UserStory, StoryStatus
from app.schemas import UserStoryCreate


def create_user_story(
    db: Session,
    story_data: dict,
    file_name: str,
    file_path: str,
    file_size_bytes: int
) -> UserStory:
    """
    Create a new user story in the database.
    
    Args:
        db: Database session
        story_data: Dictionary containing story fields
        file_name: Name of the uploaded file
        file_path: Path where file is stored
        file_size_bytes: Size of the file in bytes
        
    Returns:
        The created UserStory object 
    """
    # Create new UserStory instance
    db_story = UserStory(
        project_name=story_data["project_name"],
        release_number=story_data["release_number"],
        sprint_number=story_data["sprint_number"],
        story_pointer=story_data["story_pointer"],
        assignee=story_data["assignee"],
        reviewer=story_data["reviewer"],
        title=story_data["title"],
        description=story_data.get("description"),
        status=story_data.get("status", StoryStatus.TODO),
        file_name=file_name,
        file_path=file_path,
        file_size_bytes=file_size_bytes
    )
    
    # Add to session and commit
    db.add(db_story)
    db.commit()
    
    # Refresh to get database-generated values (id, timestamps)
    db.refresh(db_story)
    
    return db_story


def get_user_story_by_id(db: Session, story_id: int) -> Optional[UserStory]:
    """
    Retrieve a single user story by its ID.
    
    Args:
        db: Database session
        story_id: The ID of the story to retrieve
        
    Returns:
        UserStory object if found, None otherwise
    """
    return db.query(UserStory).filter(UserStory.id == story_id).first()


def get_all_user_stories(
    db: Session, 
    skip: int = 0, 
    limit: int = 100
) -> List[UserStory]:
    """
    Retrieve all user stories with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
    Returns:
        List of UserStory objects
    """
    return (
        db.query(UserStory)
        .order_by(desc(UserStory.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_user_stories_by_project(
    db: Session, 
    project_name: str
) -> List[UserStory]:
    """
    Retrieve all user stories for a specific project.
    
    Args:
        db: Database session
        project_name: Name of the project to filter by
        
    Returns:
        List of UserStory objects for the project
    """
    return (
        db.query(UserStory)
        .filter(UserStory.project_name == project_name)
        .order_by(desc(UserStory.created_at))
        .all()
    )


def get_user_stories_by_status(
    db: Session, 
    status: StoryStatus
) -> List[UserStory]:
    """
    Retrieve all user stories with a specific status.
    
    Args:
        db: Database session
        status: Status to filter by
        
    Returns:
        List of UserStory objects with the specified status
    """
    return (
        db.query(UserStory)
        .filter(UserStory.status == status)
        .order_by(desc(UserStory.created_at))
        .all()
    )


def update_user_story(
    db: Session,
    story_id: int,
    update_data: dict
) -> Optional[UserStory]:
    """
    Update an existing user story.
    
    Args:
        db: Database session
        story_id: ID of the story to update
        update_data: Dictionary of fields to update
        
    Returns:
        Updated UserStory object if found, None otherwise
    """
    db_story = get_user_story_by_id(db, story_id)
    
    if not db_story:
        return None
    
    # Update only provided fields
    for key, value in update_data.items():
        if hasattr(db_story, key) and value is not None:
            setattr(db_story, key, value)
    
    db.commit()
    db.refresh(db_story)
    
    return db_story


def delete_user_story(db: Session, story_id: int) -> bool:
    """
    Delete a user story by ID.
    
    Args:
        db: Database session
        story_id: ID of the story to delete
        
    Returns:
        True if story was deleted, False if not found
    """
    db_story = get_user_story_by_id(db, story_id)
    
    if not db_story:
        return False
    
    db.delete(db_story)
    db.commit()
    
    return True


def count_user_stories(db: Session) -> int:
    """
    Get total count of user stories.
    
    Args:
        db: Database session
        
    Returns:
        Total number of user stories
    """
    return db.query(UserStory).count()