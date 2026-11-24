import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config.settings import settings
from app.core.database.session import get_db
from app.shared.identity import RevokedToken, User, RoleAssignment
from app.shared.types import Principal, Role

_password_hasher = PasswordHasher()
_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def validate_password_policy(password: str, username: Optional[str] = None) -> None:
    if len(password) < 10:
        raise ValueError("password_too_short")
    if len(password) > 128:
        raise ValueError("password_too_long")
    if not any(ch.islower() for ch in password):
        raise ValueError("password_needs_lowercase")
    if not any(ch.isupper() for ch in password):
        raise ValueError("password_needs_uppercase")
    if not any(ch.isdigit() for ch in password):
        raise ValueError("password_needs_digit")
    if username and password.casefold() == username.casefold():
        raise ValueError("password_equals_username")


def create_access_token(
    user_id: uuid.UUID,
    role: Optional[Role],
    school_id: Optional[uuid.UUID],
    expires_delta: Optional[timedelta] = None,
    *,
    jti: Optional[str] = None,
    password_changed_at: Optional[datetime] = None,
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes))
    payload = {
        "sub": str(user_id),
        "role": role.value if role else None,
        "school_id": str(school_id) if school_id else None,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": now,
        "exp": expire,
        "jti": jti or str(uuid.uuid4()),
    }
    if password_changed_at is not None:
        payload["pwd_ts"] = password_changed_at.astimezone(timezone.utc).isoformat()
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token") from exc


def _is_revoked(db: Session, jti: str) -> bool:
    return db.execute(select(RevokedToken.id).where(RevokedToken.jti == jti)).first() is not None


def revoke_token(db: Session, payload: dict) -> RevokedToken:
    jti = payload.get("jti")
    sub = payload.get("sub")
    if not jti or not sub:
        raise ValueError("invalid_token_payload")
    expires_at = datetime.fromtimestamp(float(payload["exp"]), tz=timezone.utc)
    record = RevokedToken(
        jti=str(jti),
        user_id=uuid.UUID(str(sub)),
        expires_at=expires_at,
        revoked_at=datetime.now(timezone.utc),
    )
    db.add(record)
    db.flush()
    return record


def revoke_all_for_user(db: Session, user_id: uuid.UUID) -> None:
    user = db.get(User, user_id)
    if user is None:
        raise ValueError("user_not_found")
    user.password_changed_at = datetime.now(timezone.utc)
    db.flush()


def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise ValueError("invalid_current_password")
    validate_password_policy(new_password, user.username)
    user.password_hash = hash_password(new_password)
    user.password_changed_at = datetime.now(timezone.utc)
    user.failed_login_count = 0
    user.locked_until = None
    db.flush()


def get_current_principal(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Principal:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing_credentials")
    payload = decode_access_token(credentials.credentials)
    sub = payload.get("sub")
    jti = payload.get("jti")
    if not sub or not jti:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token")
    if _is_revoked(db, str(jti)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token_revoked")
    user_id = uuid.UUID(sub)
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="inactive_user")
    if user.password_changed_at is not None:
        token_ts = payload.get("pwd_ts")
        expected = user.password_changed_at.astimezone(timezone.utc).isoformat()
        if token_ts != expected:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token_expired_by_password_change")
    # Never trust a long-lived JWT role claim as current authorization: roles may be revoked.
    school_id = user.school_id
    token_school = payload.get("school_id")
    if token_school and str(school_id) != str(token_school):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token_school_mismatch")
    role_str = payload.get("role")
    now = datetime.now(timezone.utc)
    stmt = select(RoleAssignment).where(
        RoleAssignment.user_id == user_id,
        RoleAssignment.school_id == school_id,
        RoleAssignment.valid_from <= now,
        (RoleAssignment.valid_to.is_(None) | (RoleAssignment.valid_to > now)),
    )
    if role_str:
        stmt = stmt.where(RoleAssignment.role == role_str)
    assignment = db.execute(stmt).scalars().first()
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="role_revoked")
    try:
        role = Role(assignment.role)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_role_assignment") from exc
    return Principal(user_id=user_id, role=role, school_id=school_id)
