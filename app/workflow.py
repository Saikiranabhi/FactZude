import os
import asyncio
from functools import partial
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from .prompts import FACT_CHECK_PROMPT
from .models import FactCheckResponse, Source

# Fallback chain — tries each model in order if rate limit is hit
MODELS = [
    "llama-3.3-70b-versatile",
    "llama3-8b-8192",
    "gemma2-9b-it",
    "mixtral-8x7b-32768",
]

async def invoke_with_fallback(prompt: str) -> str:
    """Try each model in MODELS list, falling back on rate limit errors."""
    last_error = None
    for model in MODELS:
        try:
            groq = ChatGroq(
                api_key=os.getenv("GROQ_API_KEY"),
                model=model
            )
            response = await groq.ainvoke(prompt)
            print(f"[FactZude] Using model: {model}")
            return response.content
        except Exception as e:
            if "rate_limit_exceeded" in str(e) or "429" in str(e):
                print(f"[FactZude] {model} rate limited, trying next...")
                last_error = e
                continue
            raise e  # Non-rate-limit error — raise immediately
    raise Exception(f"All models hit rate limits. Last error: {last_error}")


async def run_fact_check(claim: str) -> FactCheckResponse:

    # 1. Run Tavily search in thread executor to avoid blocking async loop
    tavily = TavilySearchResults(
        tavily_api_key=os.getenv("TAVILY_API_KEY")
    )
    loop = asyncio.get_event_loop()
    evidence = await loop.run_in_executor(None, partial(tavily.run, claim))

    # 2. Build prompt and invoke LLM with model fallback
    prompt = FACT_CHECK_PROMPT.format(claim=claim, evidence=evidence)
    raw = await invoke_with_fallback(prompt)

    # 3. Extract sources from Tavily evidence
    sources = []
    if isinstance(evidence, list):
        for item in evidence:
            if isinstance(item, dict):
                sources.append(Source(
                    title=item.get("title", "Unknown"),
                    url=item.get("url", "")
                ))

    # 4. Parse verdict, confidence, explanation from LLM response
    verdict = "Uncertain"
    confidence = 0.5
    explanation = raw

    for line in raw.splitlines():
        lower = line.lower()
        if lower.startswith("verdict"):
            if "true" in lower:
                verdict = "True"
            elif "false" in lower:
                verdict = "False"
            else:
                verdict = "Uncertain"
        elif lower.startswith("confidence"):
            parts = line.split(":", 1)
            if len(parts) > 1:
                try:
                    confidence = float(parts[1].strip())
                except ValueError:
                    pass
        elif lower.startswith("explanation"):
            parts = line.split(":", 1)
            if len(parts) > 1:
                explanation = parts[1].strip()

    return FactCheckResponse(
        claim=claim,
        verdict=verdict,
        confidence=confidence,
        explanation=explanation,
        sources=sources
    )