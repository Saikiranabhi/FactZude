from pydantic import BaseModel
from typing import List

class Source(BaseModel):
    title: str
    url: str

class FactCheckResponse(BaseModel):
    claim: str
    verdict: str
    confidence: float
    explanation: str
    sources: List[Source]