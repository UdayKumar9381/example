from datetime import datetime, timedelta
from jose import jwt
import secrets
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.user import User
from app.crud.user import create_magic_link, get_magic_link_by_token, mark_magic_link_used, create_session
from app.services.mail_service import MailService
from app.schemas.auth import TokenResponse

settings = get_settings()


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.mail_service = MailService()
    
    async def send_magic_link(self, user: User):
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=settings.magic_link_expire_minutes)
        
        create_magic_link(self.db, user.id, token, expires_at)
        
        await self.mail_service.send_magic_link(user.email, token)
    
    def verify_magic_link(self, token: str) -> TokenResponse | None:
        magic_link = get_magic_link_by_token(self.db, token)
        if not magic_link:
            return None
        
        mark_magic_link_used(self.db, magic_link)
        
        access_token = self._create_access_token(magic_link.user_id)
        expires_at = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        create_session(self.db, magic_link.user_id, access_token, expires_at)
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_at=expires_at
        )
    
    def _create_access_token(self, user_id: str) -> str:
        expires = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        payload = {
            "sub": user_id,
            "exp": expires,
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)