from fastapi import APIRouter

router = APIRouter(prefix="/k01", tags=["k01"])


@router.get("/status")
def status():
    return {"module": "k01", "status": "ready"}
