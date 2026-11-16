from fastapi import APIRouter

router = APIRouter(prefix="/k04", tags=["k04"])


@router.get("/status")
def status():
    return {"module": "k04", "status": "ready"}
