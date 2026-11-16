from fastapi import APIRouter

router = APIRouter(prefix="/k03", tags=["k03"])


@router.get("/status")
def status():
    return {"module": "k03", "status": "ready"}
