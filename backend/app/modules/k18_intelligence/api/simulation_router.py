from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database.session import get_db
from app.core.security.auth import get_current_principal
from app.shared.types import Principal, Role
from app.modules.k18_intelligence.repository.store import ILStore, _to_dict
from app.modules.k18_intelligence.api.access import require_student_access, require_leadership

router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.get("/flow")
def simulation_flow(entity_id: str, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)):
    if principal is None:
        raise HTTPException(401, "auth required")
    if principal.role == Role.LEADERSHIP:
        require_leadership(db, principal, action="k18.simulation.flow")
    elif principal.role == Role.TEACHER:
        require_student_access(db, principal, entity_id, action="k18.simulation.flow")
    elif principal.role in (Role.STUDENT, Role.PARENT):
        require_student_access(db, principal, entity_id, action="k18.simulation.flow")
    else:
        raise HTTPException(403, "forbidden")
    store = ILStore(db)
    events = [_to_dict(e) for e in store.list_events(200) if (e.payload or {}).get("entity_id") == entity_id or (e.payload or {}).get("student_user_id") == entity_id]
    hyps = [_to_dict(h) for h in store.list_hypotheses(entity_id=entity_id)]
    preds = [_to_dict(p) for p in store.list_predictions(entity_id=entity_id)]
    inits = store.list_initiatives(entity_id=entity_id)
    init_ids = {str(i.id) for i in inits}
    comms = [c for c in store.list_communications() if c.get("entity_id") == entity_id]
    outs = [o for o in store.list_outcomes() if str(o.get("initiative_id")) in init_ids]
    audit = [a for a in store.list_audit(400) if a.get("entity_id") == entity_id or (a.get("details") or {}).get("entity_id") == entity_id]
    return {
        "entity_id": entity_id,
        "events": events, "hypotheses": hyps, "predictions": preds,
        "initiatives": [_to_dict(i) for i in inits], "communications": comms, "outcomes": outs, "audit": audit,
        "consistency": {
            "events": len(events), "hypotheses": len(hyps), "predictions": len(preds),
            "initiatives": len(inits), "communications": len(comms), "outcomes": len(outs),
        }
    }
