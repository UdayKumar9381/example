import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        user_id = getattr(request.state, "user_id", "anonymous")
        
        response = await call_next(request)
        
        execution_time = time.time() - start_time
        
        logger.info(
            f"method={request.method} "
            f"path={request.url.path} "
            f"user_id={user_id} "
            f"status={response.status_code} "
            f"duration={execution_time:.3f}s"
        )
        
        response.headers["X-Request-Duration"] = f"{execution_time:.3f}"
        
        return response