from fastapi import APIRouter

router = APIRouter(prefix="/k11", tags=["k11"])


@router.get("/status")
def status():
    return {"module": "k11", "status": "ready"}
