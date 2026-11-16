import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit.logger import write as audit_write
from app.core.database.session import get_db
from app.core.security.auth import create_access_token, verify_password
from app.shared.identity import RoleAssignment, User
from app.shared.types import Principal, Role

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str
    school_id: uuid.UUID | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    stmt = select(User).where(User.username == payload.username)
    if payload.school_id:
        stmt = stmt.where(User.school_id == payload.school_id)
    user = db.execute(stmt).scalars().first()
    principal = Principal(user_id=user.id if user else uuid.uuid4(), role=None, school_id=user.school_id if user else payload.school_id)
    if not user or not verify_password(payload.password, user.password_hash):
        audit_write(db, principal, action="auth.login", resource="identity_user", purpose="authentication", outcome="failure")
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")
    ra = db.execute(select(RoleAssignment).where(RoleAssignment.user_id == user.id)).scalars().first()
    role = Role(ra.role) if ra else None
    principal = Principal(user_id=user.id, role=role, school_id=user.school_id)
    token = create_access_token(user.id, role, user.school_id)
    audit_write(db, principal, action="auth.login", resource=f"identity_user:{user.id}", purpose="authentication", outcome="success")
    db.commit()
    return TokenResponse(access_token=token)
