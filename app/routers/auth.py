from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import (
    SignupRequest, 
    LoginRequest, 
    MagicLinkVerifyRequest,
    TokenResponse, 
    AuthResponse,
    UserResponse
)
from app.services.auth_service import AuthService
from app.crud.user import get_user_by_email, create_user

router = APIRouter()


@router.post("/signup", response_model=AuthResponse)
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    existing_user = get_user_by_email(db, request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = create_user(db, request)
    auth_service = AuthService(db)
    await auth_service.send_magic_link(user)
    
    return AuthResponse(
        message="Account created. Check your email for the login link.",
        email=user.email
    )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    auth_service = AuthService(db)
    await auth_service.send_magic_link(user)
    
    return AuthResponse(
        message="Magic link sent to your email",
        email=user.email
    )


@router.post("/verify", response_model=TokenResponse)
async def verify_magic_link(request: MagicLinkVerifyRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    token_data = auth_service.verify_magic_link(request.token)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired magic link"
        )
    
    return token_data


@router.post("/logout")
async def logout(db: Session = Depends(get_db)):
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(db: Session = Depends(get_db)):
    from starlette.requests import Request
    from fastapi import Request as FastAPIRequest
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Use request.state.user from middleware"
    )