from fastapi import APIRouter

router = APIRouter(prefix="/k02", tags=["k02"])


@router.get("/status")
def status():
    return {"module": "k02", "status": "ready"}
