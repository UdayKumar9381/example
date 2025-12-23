from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from jose import JWTError, jwt
from app.config import get_settings
from app.database import SessionLocal
from app.crud.user import get_user_by_id

settings = get_settings()

EXCLUDED_PATHS = [
    "/api/v1/auth/signup",
    "/api/v1/auth/login",
    "/api/v1/auth/verify",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json"
]


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if self._is_excluded_path(request.url.path):
            return await call_next(request)
        
        token = self._extract_token(request)
        if not token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing authentication token"}
            )
        
        user_data = self._verify_token(token)
        if not user_data:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"}
            )
        
        db = SessionLocal()
        try:
            user = get_user_by_id(db, user_data.get("sub"))
            if not user or not user.is_active:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "User not found or inactive"}
                )
            request.state.user = user
            request.state.user_id = user.id
            request.state.user_role = user.role
        finally:
            db.close()
        
        return await call_next(request)
    
    def _is_excluded_path(self, path: str) -> bool:
        return any(path.startswith(excluded) for excluded in EXCLUDED_PATHS)
    
    def _extract_token(self, request: Request) -> str | None:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]
        return None
    
    def _verify_token(self, token: str) -> dict | None:
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm]
            )
            return payload
        except JWTError:
            return None