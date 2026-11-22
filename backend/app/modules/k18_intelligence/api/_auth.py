from fastapi import HTTPException
from app.core.permissions.policy import authorize
from app.shared.types import Principal


def require(principal: Principal | None, action: str, resource: str, context: dict | None = None, db=None):
    ctx = dict(context or {})
    # default: authenticated users with same-school context allowed for read; write needs role checks
    if principal is None:
        raise HTTPException(status_code=401, detail="auth required")
    decision = authorize(principal, action, resource, context=ctx, db=db)
    if not decision.allowed:
        # fallback: allow authenticated same-school for intelligence read endpoints when explicitly marked
        if ctx.get("allow_authenticated_school") and principal.school_id and ctx.get("school_id") in (None, principal.school_id):
            return
        raise HTTPException(status_code=403, detail=f"forbidden:{decision.reason}")
