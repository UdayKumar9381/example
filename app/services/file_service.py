import os
import uuid
import aiofiles
from fastapi import UploadFile, HTTPException, status
from app.config import get_settings

settings = get_settings()


class FileService:
    def __init__(self):
        self.upload_dir = settings.upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)
    
    async def save_file(self, file: UploadFile, task_id: str) -> dict:
        if file.size and file.size > settings.max_upload_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed ({settings.max_upload_size} bytes)"
            )
        
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        task_dir = os.path.join(self.upload_dir, task_id)
        os.makedirs(task_dir, exist_ok=True)
        
        file_path = os.path.join(task_dir, unique_filename)
        
        content = await file.read()
        file_size = len(content)
        
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        
        return {
            "filename": file.filename,
            "file_path": file_path,
            "file_size": file_size,
            "mime_type": file.content_type
        }
    
    async def delete_file(self, file_path: str) -> bool:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    
    def get_file_path(self, task_id: str, filename: str) -> str:
        return os.path.join(self.upload_dir, task_id, filename)