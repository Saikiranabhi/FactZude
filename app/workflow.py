import os
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from .prompts import FACT_CHECK_PROMPT

groq = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="mixtral-8x7b-32768"
)

tavily = TavilySearchResults(
    tavily_api_key=os.getenv("TAVILY_API_KEY")
)

async def run_fact_check(claim: str):

    # 1. Get web evidence
    evidence = tavily.run(claim)

    # 2. LLM reasoning
    prompt = FACT_CHECK_PROMPT.format(claim=claim, evidence=evidence)
    response = groq.invoke(prompt)

    return {
        "claim": claim,
        "analysis": response.content,
        "sources": evidence
    }