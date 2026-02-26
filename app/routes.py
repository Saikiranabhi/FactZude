# from fastapi import APIRouter
# from pydantic import BaseModel
# from .workflow import run_fact_check

# router = APIRouter()

# class ClaimRequest(BaseModel):
#     claim: str

# @router.post("/fact-check")
# async def fact_check(data: ClaimRequest):
#     result = await run_fact_check(data.claim)
#     return result


from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .workflow import run_fact_check
from .models import FactCheckResponse

router = APIRouter()

class ClaimRequest(BaseModel):
    claim: str

@router.post("/fact-check", response_model=FactCheckResponse)
async def fact_check(data: ClaimRequest):
    if not data.claim or not data.claim.strip():
        raise HTTPException(status_code=400, detail="Claim cannot be empty.")
    try:
        result = await run_fact_check(data.claim)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fact check failed: {str(e)}")