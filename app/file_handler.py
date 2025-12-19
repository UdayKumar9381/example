# app/file_handler.py
"""
File handling utilities for upload operations.
Manages file storage, validation, and metadata extraction.
"""

import os
import shutil
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile, HTTPException, status
from app.config import get_settings

settings = get_settings()


def format_file_size(size_bytes: int) -> str:
    """
    Convert bytes to human-readable format.
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        Formatted string (e.g., "2.5 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def ensure_upload_directory() -> Path:
    """
    Ensure the upload directory exists.
    Creates it if necessary.
    
    Returns:
        Path object to upload directory
    """
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path


def validate_file(file: UploadFile) -> None:
    """
    Validate uploaded file.
    
    Args:
        file: The uploaded file to validate
        
    Raises:
        HTTPException: If file is invalid
    """
    # Check if file is provided
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Support document is mandatory. Please upload a file."
        )
    
    # Check filename validity
    if file.filename.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file name."
        )


async def save_upload_file(file: UploadFile) -> Tuple[str, str, int, bool]:
    """
    Save uploaded file to the uploads directory.
    
    Args:
        file: The uploaded file from the request
        
    Returns:
        Tuple containing:
        - file_name: Original file name
        - file_path: Path where file is saved
        - file_size: Size of file in bytes
        - override: True if existing file was replaced
        
    Raises:
        HTTPException: If file validation fails or save operation fails
    """
    # Validate the file
    validate_file(file)
    
    # Ensure upload directory exists
    upload_dir = ensure_upload_directory()
    
    # Sanitize filename (remove potentially dangerous characters)
    safe_filename = os.path.basename(file.filename)
    file_path = upload_dir / safe_filename
    
    # Check if file already exists (for override flag)
    file_existed = file_path.exists()
    
    try:
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Validate file size
        if file_size > settings.max_file_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed size of {settings.max_file_size_mb} MB"
            )
        
        # Check for empty file
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot upload empty file."
            )
        
        # Write file to disk (overwrites if exists)
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        return (
            safe_filename,
            str(file_path),
            file_size,
            file_existed  # override flag
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    finally:
        # Reset file pointer for potential reuse
        await file.seek(0)


def delete_file(file_path: str) -> bool:
    """
    Delete a file from the filesystem.
    
    Args:
        file_path: Path to the file to delete
        
    Returns:
        True if file was deleted, False if it didn't exist
    """
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            return True
        return False
    except Exception:
        return False


def get_file_path(filename: str) -> Path:
    """
    Get the full path for a file in the uploads directory.
    
    Args:
        filename: Name of the file
        
    Returns:
        Full path to the file
    """
    return Path(settings.upload_dir) / filename