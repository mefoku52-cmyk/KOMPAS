from fastapi import APIRouter

router = APIRouter(prefix="/k08", tags=["k08"])


@router.get("/status")
def status():
    return {"module": "k08", "status": "ready"}
