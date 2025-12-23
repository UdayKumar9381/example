import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.config import get_settings

settings = get_settings()

RATE_LIMITED_PATHS = [
    "/api/v1/auth",
    "/api/v1/search"
]


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.request_counts = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        if not self._should_rate_limit(request.url.path):
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        identifier = f"{client_ip}:{request.url.path}"
        
        if self._is_rate_limited(identifier):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."}
            )
        
        self._record_request(identifier)
        
        return await call_next(request)
    
    def _should_rate_limit(self, path: str) -> bool:
        return any(path.startswith(limited) for limited in RATE_LIMITED_PATHS)
    
    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _is_rate_limited(self, identifier: str) -> bool:
        current_time = time.time()
        window_start = current_time - settings.rate_limit_window
        
        self.request_counts[identifier] = [
            timestamp for timestamp in self.request_counts[identifier]
            if timestamp > window_start
        ]
        
        return len(self.request_counts[identifier]) >= settings.rate_limit_requests
    
    def _record_request(self, identifier: str):
        self.request_counts[identifier].append(time.time())