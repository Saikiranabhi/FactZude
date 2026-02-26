import os
import asyncio
from functools import partial
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from .prompts import FACT_CHECK_PROMPT
from .models import FactCheckResponse, Source

async def run_fact_check(claim: str) -> FactCheckResponse:

    # Initialize clients inside function so env vars are already loaded
    groq = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model="llama-3.3-70b-versatile"
    )
    tavily = TavilySearchResults(
        tavily_api_key=os.getenv("TAVILY_API_KEY")
    )

    # 1. Run synchronous Tavily search in thread executor to avoid blocking async loop
    loop = asyncio.get_event_loop()
    evidence = await loop.run_in_executor(None, partial(tavily.run, claim))

    # 2. Use async invoke for LLM to avoid blocking
    prompt = FACT_CHECK_PROMPT.format(claim=claim, evidence=evidence)
    response = await groq.ainvoke(prompt)

    # 3. Parse structured response from LLM output
    raw = response.content

    # Extract sources from Tavily evidence
    sources = []
    if isinstance(evidence, list):
        for item in evidence:
            if isinstance(item, dict):
                sources.append(Source(
                    title=item.get("title", "Unknown"),
                    url=item.get("url", "")
                ))

    # Parse verdict, confidence, explanation from LLM response
    verdict = "Uncertain"
    confidence = 0.5
    explanation = raw

    lines = raw.splitlines()
    for line in lines:
        lower = line.lower()
        if "verdict" in lower:
            if "true" in lower:
                verdict = "True"
            elif "false" in lower:
                verdict = "False"
            else:
                verdict = "Uncertain"
        elif "confidence" in lower:
            # Extract float from line e.g. "Confidence Score: 0.85"
            parts = line.split(":")
            if len(parts) > 1:
                try:
                    confidence = float(parts[1].strip())
                except ValueError:
                    pass
        elif "explanation" in lower:
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