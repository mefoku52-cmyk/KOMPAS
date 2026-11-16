from fastapi import APIRouter

router = APIRouter(prefix="/k16", tags=["k16"])


@router.get("/status")
def status():
    return {"module": "k16", "status": "ready"}
