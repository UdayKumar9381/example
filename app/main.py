# app/main.py
"""
FastAPI Application Entry Point.

This is the main module that:
- Creates the FastAPI application instance
- Configures middleware and exception handlers
- Includes routers for different endpoints
- Initializes the database on startup
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.database import init_db
from app.routers import user_stories

# new loadidihbvid
# Load application settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Startup:
    - Initialize database tables
    - Create upload directory
    
    Shutdown:
    - Cleanup resources if needed
    """
    # Startup
    print("🚀 Starting User Story Manager API...")
    
    # Initialize database tables
    init_db()
    print("✅ Database initialized successfully")
    
    # Ensure upload directory exists
    from app.file_handler import ensure_upload_directory
    ensure_upload_directory()
    print(f"✅ Upload directory ready: {settings.upload_dir}/")
    
    yield  # Application runs here
    
    # Shutdown
    print("👋 Shutting down User Story Manager API...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
    ## User Story Management API
    
    A production-grade backend API for managing user stories with file upload support.
    
    ### Features:
    - **Create User Stories**: Add new stories with mandatory support documents
    - **File Management**: Upload files with automatic override detection
    - **Retrieve Stories**: Get individual or all stories with file metadata
    
    ### Technical Stack:
    - FastAPI (Python web framework)
    - SQLAlchemy (ORM)
    - MySQL (Database)
    
    ### File Upload Rules:
    - Support document is **mandatory**
    - Files are saved in the `uploads/` directory
    - If a file with the same name exists, it is **overwritten**
    - Response includes `override: true/false` flag
    """,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",          # Swagger UI
    redoc_url="/redoc",        # ReDoc UI
    openapi_url="/openapi.json"
)


# Configure CORS (Cross-Origin Resource Sharing)
# This allows the HTML frontend to communicate with the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Allow all origins (configure for production)
    allow_credentials=True,
    allow_methods=["*"],        # Allow all HTTP methods
    allow_headers=["*"],        # Allow all headers
)


# Include routers
app.include_router(user_stories.router)


# Root endpoint - API health check
@app.get(
    "/",
    tags=["Health"],
    summary="API Health Check",
    description="Returns API status and version information"
)
def root():
    """
    Root endpoint for health checks.
    Returns basic API information.
    """
    return {
        "status": "healthy",
        "api_name": settings.app_name,
        "version": settings.app_version,
        "message": "Welcome to User Story Manager API",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc"
        }
    }


# Global exception handler for unhandled errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler for unexpected errors.
    Logs the error and returns a generic error response.
    """
    # In production, log this error
    print(f"❌ Unexpected error: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "An unexpected error occurred",
            "detail": str(exc) if settings.debug else "Please contact support"
        }
    )


# Health check endpoint for monitoring
@app.get(
    "/health",
    tags=["Health"],
    summary="Detailed Health Check"
)
def health_check():
    """
    Detailed health check for monitoring systems.
    """
    return {
        "status": "healthy",
        "database": "connected",
        "upload_directory": settings.upload_dir
    }