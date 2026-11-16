from fastapi import APIRouter

router = APIRouter(prefix="/k10", tags=["k10"])


@router.get("/status")
def status():
    return {"module": "k10", "status": "ready"}
