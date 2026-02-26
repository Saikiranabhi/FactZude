# from pydantic import BaseModel
# from typing import List

# class Source(BaseModel):
#     title: str
#     url: str

# class FactCheckResponse(BaseModel):
#     claim: str
#     verdict: str
#     confidence: float
#     explanation: str
#     sources: List[Source]


from pydantic import BaseModel, Field
from typing import List

class Source(BaseModel):
    title: str
    url: str

class FactCheckResponse(BaseModel):
    claim: str
    verdict: str                          # "True", "False", or "Uncertain"
    confidence: float = Field(ge=0, le=1) # Clamped between 0 and 1
    explanation: str
    sources: List[Source]