from fastapi import HTTPException, status


class BaseAPIException(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class NotFoundException(BaseAPIException):
    def __init__(self, resource: str, resource_id: int | str):
        super().__init__(
            detail=f"{resource} with id '{resource_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND
        )


class BadRequestException(BaseAPIException):
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class ValidationException(BaseAPIException):
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class FileUploadException(BaseAPIException):
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)