from fastapi import APIRouter

router = APIRouter(prefix="/k05", tags=["k05"])


@router.get("/status")
def status():
    return {"module": "k05", "status": "ready"}
