from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta
from uuid import uuid4

from app.models.user import User, MagicLink, Session as UserSession
from app.schemas.auth import SignupRequest


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: str) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user_data: SignupRequest) -> User:
    user = User(
        id=str(uuid4()),
        email=user_data.email,
        display_name=user_data.display_name
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: str, update_data: dict) -> User | None:
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    
    for key, value in update_data.items():
        if value is not None:
            setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    return user


def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    return db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()


def search_users(db: Session, query: str, limit: int = 10) -> list[User]:
    return db.query(User).filter(
        User.is_active == True,
        or_(
            User.email.ilike(f"%{query}%"),
            User.display_name.ilike(f"%{query}%")
        )
    ).limit(limit).all()


def create_magic_link(db: Session, user_id: str, token: str, expires_at: datetime) -> MagicLink:
    magic_link = MagicLink(
        id=str(uuid4()),
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    db.add(magic_link)
    db.commit()
    db.refresh(magic_link)
    return magic_link


def get_magic_link_by_token(db: Session, token: str) -> MagicLink | None:
    return db.query(MagicLink).filter(
        MagicLink.token == token,
        MagicLink.is_used == False,
        MagicLink.expires_at > datetime.utcnow()
    ).first()


def mark_magic_link_used(db: Session, magic_link: MagicLink):
    magic_link.is_used = True
    db.commit()


def create_session(db: Session, user_id: str, token: str, expires_at: datetime) -> UserSession:
    session = UserSession(
        id=str(uuid4()),
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def delete_user_sessions(db: Session, user_id: str):
    db.query(UserSession).filter(UserSession.user_id == user_id).delete()
    db.commit()