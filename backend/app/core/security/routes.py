import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit.logger import write as audit_write
from app.core.config.settings import settings
from app.core.database.session import get_db
from app.core.errors import AppError
from app.core.ratelimit import check_login_rate_limit
from app.core.security.auth import (
    change_password,
    create_access_token,
    decode_access_token,
    get_current_principal,
    revoke_token,
    validate_password_policy,
    verify_password,
)
from app.shared.identity import RoleAssignment, User
from app.shared.types import Principal, Role

router = APIRouter(prefix="/auth", tags=["auth"])
_bearer = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    username: str
    password: str
    school_id: uuid.UUID | None = None
    role: Role | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    client_host = request.client.host if request.client else None
    rate = check_login_rate_limit(payload.username, client_host)
    principal = Principal(user_id=uuid.uuid4(), role=None, school_id=payload.school_id)
    if not rate.allowed:
        audit_write(db, principal, action="auth.login", resource="identity_user", purpose="authentication", outcome="rate_limited", details={"retry_after": rate.retry_after_seconds})
        db.commit()
        raise AppError(429, "rate_limited", "rate_limited", {"retry_after_seconds": rate.retry_after_seconds})

    stmt = select(User).where(User.username == payload.username)
    if payload.school_id:
        stmt = stmt.where(User.school_id == payload.school_id)
    user = db.execute(stmt).scalars().first()
    principal = Principal(user_id=user.id if user else uuid.uuid4(), role=None, school_id=user.school_id if user else payload.school_id)

    if user is not None and user.locked_until is not None:
        locked_until = user.locked_until
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        if locked_until > datetime.now(timezone.utc):
            audit_write(db, principal, action="auth.login", resource=f"identity_user:{user.id}", purpose="authentication", outcome="locked")
            db.commit()
            raise AppError(429, "account_locked", "account_locked", {"locked_until": locked_until.isoformat()})

    if not user or not verify_password(payload.password, user.password_hash):
        if user is not None:
            user.failed_login_count = int(user.failed_login_count or 0) + 1
            locked = user.failed_login_count >= settings.login_max_failures
            if locked:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.login_lockout_minutes)
            audit_write(
                db, principal, action="auth.login", resource=f"identity_user:{user.id}",
                purpose="authentication", outcome="failure",
                details={"failed_login_count": user.failed_login_count, "locked": locked},
            )
        else:
            audit_write(db, principal, action="auth.login", resource="identity_user", purpose="authentication", outcome="failure")
        db.commit()
        if user is not None and user.locked_until is not None:
            raise AppError(429, "account_locked", "account_locked", {"locked_until": user.locked_until.isoformat()})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")

    user.failed_login_count = 0
    user.locked_until = None
    role_stmt = select(RoleAssignment).where(
        RoleAssignment.user_id == user.id,
        RoleAssignment.school_id == user.school_id,
        RoleAssignment.valid_from <= datetime.now(timezone.utc),
        (RoleAssignment.valid_to.is_(None) | (RoleAssignment.valid_to > datetime.now(timezone.utc))),
    )
    if payload.role is not None:
        role_stmt = role_stmt.where(RoleAssignment.role == payload.role.value)
    assignments = db.execute(role_stmt).scalars().all()
    if not assignments:
        db.rollback()
        raise HTTPException(status_code=403, detail="no_active_role_assignment")
    if payload.role is None and len(assignments) > 1:
        db.rollback()
        raise HTTPException(status_code=409, detail="role_selection_required")
    role = Role(assignments[0].role)
    principal = Principal(user_id=user.id, role=role, school_id=user.school_id)
    token = create_access_token(user.id, role, user.school_id, password_changed_at=user.password_changed_at)
    audit_write(db, principal, action="auth.login", resource=f"identity_user:{user.id}", purpose="authentication", outcome="success")
    db.commit()
    return TokenResponse(access_token=token, expires_in=settings.jwt_access_token_expire_minutes * 60)


@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing_credentials")
    payload = decode_access_token(credentials.credentials)
    try:
        revoke_token(db, payload)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token")
    audit_write(db, principal, action="auth.logout", resource=f"identity_user:{principal.user_id}", purpose="authentication", outcome="success")
    db.commit()
    return {"status": "logged_out"}


@router.post("/change-password")
def change_password_route(
    payload: ChangePasswordRequest,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    user = db.get(User, principal.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="inactive_user")
    validate_password_policy(payload.new_password, user.username)
    change_password(db, user, payload.current_password, payload.new_password)
    audit_write(db, principal, action="auth.change_password", resource=f"identity_user:{user.id}", purpose="authentication", outcome="success")
    db.commit()
    return {"status": "password_changed"}
