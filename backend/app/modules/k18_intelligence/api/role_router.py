from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database.session import get_db
from app.core.security.auth import get_current_principal
from app.shared.types import Principal, Role
from app.modules.k18_intelligence.repository.store import ILStore, _to_dict
from app.modules.k18_intelligence.api.access import require_leadership, require_student_access, can_access_student, filter_initiatives_for_principal

router = APIRouter(prefix="/intelligence/roles", tags=["intelligence-roles"])
SAFE_ROLES = {"student","parent","teacher","leadership","specialist","admin"}

@router.get("/dashboard")
def role_dashboard(role: str = Query(...), entity_id: str | None = Query(None), db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    if role not in SAFE_ROLES:
        raise HTTPException(400, "unknown role")
    if principal is None:
        raise HTTPException(401, "auth required")
    # principal can only request their own role view, except leadership/admin/specialist mapped by role
    p_role = principal.role.value if hasattr(principal.role, "value") else str(principal.role)
    if p_role != role and not principal.is_system:
        # leadership can view leadership/admin aggregates; others denied
        if not (principal.role == Role.LEADERSHIP and role in {"leadership","admin"}):
            raise HTTPException(403, "forbidden")

    store = ILStore(db)
    inits = store.list_initiatives(entity_id=entity_id)
    inits = filter_initiatives_for_principal(db, principal, inits)
    comms = store.list_communications()
    preds = store.list_predictions(entity_id=entity_id)
    audit = store.list_audit(100)

    if role == "student":
        if not entity_id:
            entity_id = str(principal.user_id)
        require_student_access(db, principal, entity_id)
        safe_comms = [c for c in comms if c.get("entity_id")==entity_id]
        return {"role":"student","entity_id":entity_id,"notifications":[{"id":c["id"],"text":c.get("payload",{}).get("text"),"status":c["status"]} for c in safe_comms], "has_support": any(i.decision in ("act","request_more") for i in inits)}
    if role == "parent":
        if not entity_id:
            raise HTTPException(400, "entity_id required")
        require_student_access(db, principal, entity_id)
        safe_comms = [c for c in comms if c.get("entity_id")==entity_id]
        return {"role":"parent","entity_id":entity_id,"notifications":[{"id":c["id"],"text":c.get("payload",{}).get("text"),"status":c["status"]} for c in safe_comms], "has_support": any(i.decision in ("act","request_more") for i in inits), "uncertainty": _to_dict(preds[0])["uncertainty"] if preds else "unknown"}
    if role == "teacher":
        signals = [_to_dict(i) for i in inits if i.decision in ("act","request_more","observe")]
        teacher_comms = [c for c in comms if c.get("recipient_role")=="teacher" and (c.get("entity_type")!="student" or can_access_student(db, principal, c.get("entity_id")))]
        return {"role":"teacher","signals":signals, "notifications":teacher_comms}
    if role == "leadership":
        require_leadership(db, principal, action="k18.dashboard.leadership")
        return {"role":"leadership","signals":[_to_dict(i) for i in inits], "predictions":[_to_dict(p) for p in preds], "audit":audit[:50], "counts":{"initiatives":len(inits),"communications":len(comms)}}
    if role == "specialist":
        require_leadership(db, principal, action="k18.dashboard.specialist")
        return {"role":"specialist","signals":[_to_dict(i) for i in inits], "hypotheses":[_to_dict(h) for h in store.list_hypotheses(entity_id=entity_id)], "predictions":[_to_dict(p) for p in preds], "audit":audit[:50]}
    if role == "admin":
        require_leadership(db, principal, action="k18.dashboard.admin")
        return {"role":"admin","config_endpoint":"/intelligence/admin/config","health_endpoint":"/intelligence/admin/health","audit":audit[:50]}
    raise HTTPException(400, "unsupported role")
