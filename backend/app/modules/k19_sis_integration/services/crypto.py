from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config.settings import settings


class SecretCryptoError(ValueError):
    pass


def _fernet() -> Fernet:
    secret = (settings.sis_secret_key or settings.jwt_secret_key or "").strip()
    if not secret:
        raise SecretCryptoError("missing_sis_secret_key")
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest())
    return Fernet(key)


def encrypt_secret(value: str) -> str:
    if not value:
        raise SecretCryptoError("empty_secret")
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(token: str) -> str:
    if not token:
        raise SecretCryptoError("empty_secret")
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise SecretCryptoError("invalid_secret_token") from exc


def mask_secret(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 6:
        return "*" * len(value)
    return f"{value[:2]}***{value[-2:]}"
