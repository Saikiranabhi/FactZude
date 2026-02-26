from fastapi import APIRouter
from pydantic import BaseModel
from .workflow import run_fact_check

router = APIRouter()

class ClaimRequest(BaseModel):
    claim: str

@router.post("/fact-check")
async def fact_check(data: ClaimRequest):
    result = await run_fact_check(data.claim)
    return result