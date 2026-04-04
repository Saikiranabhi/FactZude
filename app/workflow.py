# import os
# import asyncio
# from functools import partial
# from langchain_groq import ChatGroq
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_community.tools.tavily_search import TavilySearchResults
# from .prompts import FACT_CHECK_PROMPT
# from .models import FactCheckResponse, Source

# # ── Groq models (tried in order) ──
# GROQ_MODELS = [
#     "llama-3.3-70b-versatile",
#     "llama3-8b-8192",
#     "gemma2-9b-it",
#     "mixtral-8x7b-32768",
# ]

# async def invoke_groq(prompt: str) -> str:
#     last_error = None
#     for model in GROQ_MODELS:
#         try:
#             groq = ChatGroq(
#                 api_key=os.getenv("GROQ_API_KEY"),
#                 model=model
#             )
#             response = await groq.ainvoke(prompt)
#             print(f"[FactZude] Using Groq model: {model}")
#             return response.content
#         except Exception as e:
#             if "rate_limit_exceeded" in str(e) or "429" in str(e) or "restricted" in str(e):
#                 print(f"[FactZude] {model} failed, trying next...")
#                 last_error = e
#                 continue
#             raise e
#     raise Exception(f"All Groq models failed: {last_error}")


# async def invoke_gemini(prompt: str) -> str:
#     try:
#         gemini = ChatGoogleGenerativeAI(
#             model="gemini-1.5-flash",          # free tier available
#             google_api_key=os.getenv("GEMINI_API_KEY")
#         )
#         response = await gemini.ainvoke(prompt)
#         print("[FactZude] Using fallback: Gemini")
#         return response.content
#     except Exception as e:
#         raise Exception(f"Gemini fallback also failed: {e}")


# async def invoke_with_fallback(prompt: str) -> str:
#     try:
#         return await invoke_groq(prompt)
#     except Exception as groq_error:
#         print(f"[FactZude] Groq fully failed: {groq_error} — switching to Gemini...")
#         return await invoke_gemini(prompt)         # ← fallback kicks in here


# async def run_fact_check(claim: str) -> FactCheckResponse:

#     tavily = TavilySearchResults(
#         tavily_api_key=os.getenv("TAVILY_API_KEY")
#     )
#     loop = asyncio.get_event_loop()
#     evidence = await loop.run_in_executor(None, partial(tavily.run, claim))

#     prompt = FACT_CHECK_PROMPT.format(claim=claim, evidence=evidence)
#     raw = await invoke_with_fallback(prompt)

#     sources = []
#     if isinstance(evidence, list):
#         for item in evidence:
#             if isinstance(item, dict):
#                 sources.append(Source(
#                     title=item.get("title", "Unknown"),
#                     url=item.get("url", "")
#                 ))

#     verdict     = "Uncertain"
#     confidence  = 0.5
#     explanation = raw

#     for line in raw.splitlines():
#         lower = line.lower()
#         if lower.startswith("verdict"):
#             if "true" in lower:
#                 verdict = "True"
#             elif "false" in lower:
#                 verdict = "False"
#             else:
#                 verdict = "Uncertain"
#         elif lower.startswith("confidence"):
#             parts = line.split(":", 1)
#             if len(parts) > 1:
#                 try:
#                     confidence = float(parts[1].strip())
#                 except ValueError:
#                     pass
#         elif lower.startswith("explanation"):
#             parts = line.split(":", 1)
#             if len(parts) > 1:
#                 explanation = parts[1].strip()

#     return FactCheckResponse(
#         claim=claim,
#         verdict=verdict,
#         confidence=confidence,
#         explanation=explanation,
#         sources=sources
#     )
# # ```

# # ---

# # Add to `requirements.txt`:
# # ```
# # langchain-google-genai
# # ```

# # Add to `.env`:
# # ```
# # GEMINI_API_KEY=your_gemini_api_key_here
# # ```

# # Get free Gemini key at: **aistudio.google.com**

# # ---

# # **Flow summary:**
# # ```
# # Groq llama-3.3-70b → fails
# # Groq llama3-8b     → fails
# # Groq gemma2-9b     → fails
# # Groq mixtral       → fails
# #         ↓
# # Gemini 1.5 Flash   → responds ✅


import os
import asyncio
import json
import re
from functools import partial

# ── Lazy imports (loaded only when needed) ──────────────────────────────────
from .prompts import FACT_CHECK_PROMPT
from .models import FactCheckResponse, Source


# ════════════════════════════════════════════════════════════════════════════
#  TIER 1 — Groq (fast, cloud)
# ════════════════════════════════════════════════════════════════════════════
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama3-8b-8192",
    "gemma2-9b-it",
    "mixtral-8x7b-32768",
]

async def _try_groq(prompt: str) -> str | None:
    """Return LLM text or None on failure."""
    groq_key = os.getenv("GROQ_API_KEY", "")
    if not groq_key:
        return None

    try:
        from langchain_groq import ChatGroq
    except ImportError:
        print("[FactZude] langchain_groq not installed – skipping Groq tier")
        return None

    for model in GROQ_MODELS:
        try:
            llm = ChatGroq(api_key=groq_key, model=model)
            response = await llm.ainvoke(prompt)
            print(f"[FactZude] ✅ Groq · {model}")
            return response.content
        except Exception as e:
            err = str(e)
            if any(k in err for k in ("rate_limit", "429", "suspended", "blocked", "policy")):
                print(f"[FactZude] ⚠️  Groq/{model} skipped: {err[:80]}")
                continue
            print(f"[FactZude] ❌ Groq/{model} error: {err[:120]}")
            continue  # try next model instead of raising

    return None  # all Groq models failed


# ════════════════════════════════════════════════════════════════════════════
#  TIER 2 — Google Gemini (cloud)
# ════════════════════════════════════════════════════════════════════════════
GEMINI_MODELS = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-pro",
]

async def _try_gemini(prompt: str) -> str | None:
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if not gemini_key:
        print("[FactZude] GEMINI_API_KEY not set – skipping Gemini tier")
        return None

    try:
        import google.generativeai as genai  # pip install google-generativeai
    except ImportError:
        print("[FactZude] google-generativeai not installed – skipping Gemini tier")
        return None

    genai.configure(api_key=gemini_key)

    for model_name in GEMINI_MODELS:
        try:
            model = genai.GenerativeModel(model_name)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, lambda: model.generate_content(prompt)
            )
            text = response.text.strip()
            if text:
                print(f"[FactZude] ✅ Gemini · {model_name}")
                return text
        except Exception as e:
            err = str(e)
            if any(k in err for k in ("quota", "429", "RESOURCE_EXHAUSTED", "blocked")):
                print(f"[FactZude] ⚠️  Gemini/{model_name} skipped: {err[:80]}")
                continue
            print(f"[FactZude] ❌ Gemini/{model_name} error: {err[:120]}")
            continue

    return None


# ════════════════════════════════════════════════════════════════════════════
#  TIER 3 — Ollama TinyLlama (local)
# ════════════════════════════════════════════════════════════════════════════
OLLAMA_MODELS = ["tinyllama", "llama3", "mistral", "phi3"]
OLLAMA_URL    = os.getenv("OLLAMA_URL", "http://localhost:11434")

async def _try_ollama(prompt: str) -> str | None:
    try:
        import httpx
    except ImportError:
        print("[FactZude] httpx not installed – skipping Ollama tier")
        return None

    for model in OLLAMA_MODELS:
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 512},
            }
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
                r.raise_for_status()
                text = r.json().get("response", "").strip()
                if text:
                    print(f"[FactZude] ✅ Ollama · {model}")
                    return text
        except Exception as e:
            err = str(e)
            print(f"[FactZude] ⚠️  Ollama/{model} skipped: {err[:80]}")
            continue

    return None


# ════════════════════════════════════════════════════════════════════════════
#  TIER 4 — Flan-T5 (fully offline, local HuggingFace)
# ════════════════════════════════════════════════════════════════════════════
# Kept as a last resort — slower but always available offline.
# Models in order of quality vs. speed:
#   google/flan-t5-large  (~800 MB) — best quality offline
#   google/flan-t5-base   (~250 MB) — balanced
#   google/flan-t5-small  (~80 MB)  — fastest
FLAN_MODELS = [
    "google/flan-t5-large",
    "google/flan-t5-base",
    "google/flan-t5-small",
]

_flan_pipeline = None  # cached after first load

def _load_flan(model_name: str):
    """Load (and cache) a Flan-T5 pipeline synchronously."""
    global _flan_pipeline
    if _flan_pipeline is not None:
        return _flan_pipeline
    from transformers import pipeline  # pip install transformers sentencepiece torch
    print(f"[FactZude] Loading Flan-T5 model: {model_name} (first run may be slow)…")
    _flan_pipeline = pipeline(
        "text2text-generation",
        model=model_name,
        max_new_tokens=256,
        do_sample=False,
    )
    return _flan_pipeline


def _flan_infer(prompt: str, model_name: str) -> str:
    pipe = _load_flan(model_name)
    # Flan-T5 works best with a short, instructional prefix
    short_prompt = (
        "You are a fact-checker. Analyse the claim and evidence below.\n\n"
        + prompt[:1800]   # keep within T5 token limit
    )
    results = pipe(short_prompt)
    return results[0]["generated_text"].strip()


async def _try_flan(prompt: str) -> str | None:
    for model_name in FLAN_MODELS:
        try:
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(None, _flan_infer, prompt, model_name)
            if text:
                print(f"[FactZude] ✅ Flan-T5 · {model_name}")
                return text
        except ImportError:
            print("[FactZude] transformers/torch not installed – skipping Flan-T5 tier")
            return None
        except Exception as e:
            print(f"[FactZude] ❌ Flan-T5/{model_name} error: {str(e)[:120]}")
            continue

    return None


# ════════════════════════════════════════════════════════════════════════════
#  ORCHESTRATOR  —  try all tiers in order
# ════════════════════════════════════════════════════════════════════════════
async def invoke_with_fallback(prompt: str) -> str:
    """
    Try each provider tier in order:
      Groq → Gemini → Ollama → Flan-T5 (offline)

    Raises only if every tier fails.
    """
    tiers = [
        ("Groq",    _try_groq),
        ("Gemini",  _try_gemini),
        ("Ollama",  _try_ollama),
        ("Flan-T5", _try_flan),
    ]

    for name, fn in tiers:
        try:
            result = await fn(prompt)
            if result:
                return result
        except Exception as e:
            print(f"[FactZude] Tier '{name}' raised unexpectedly: {e}")

    raise RuntimeError(
        "All LLM providers failed. "
        "Check your API keys (GROQ_API_KEY, GEMINI_API_KEY) "
        "and ensure Ollama is running locally if you need offline support."
    )


# ════════════════════════════════════════════════════════════════════════════
#  MAIN FACT-CHECK WORKFLOW
# ════════════════════════════════════════════════════════════════════════════
async def run_fact_check(claim: str) -> FactCheckResponse:

    # 1. Tavily web search ──────────────────────────────────────────────────
    from langchain_community.tools.tavily_search import TavilySearchResults

    tavily = TavilySearchResults(tavily_api_key=os.getenv("TAVILY_API_KEY"))
    loop = asyncio.get_event_loop()
    evidence = await loop.run_in_executor(None, partial(tavily.run, claim))

    # 2. Build prompt & call LLM with full fallback chain ───────────────────
    prompt = FACT_CHECK_PROMPT.format(claim=claim, evidence=evidence)
    raw    = await invoke_with_fallback(prompt)

    # 3. Extract sources ────────────────────────────────────────────────────
    sources: list[Source] = []
    if isinstance(evidence, list):
        for item in evidence:
            if isinstance(item, dict):
                sources.append(Source(
                    title=item.get("title", "Unknown"),
                    url=item.get("url", ""),
                ))

    # 4. Parse structured response ──────────────────────────────────────────
    verdict     = "Uncertain"
    confidence  = 0.5
    explanation = raw  # fallback: full raw text

    for line in raw.splitlines():
        stripped = line.strip()
        lower    = stripped.lower()

        if lower.startswith("verdict"):
            if "true" in lower:
                verdict = "True"
            elif "false" in lower:
                verdict = "False"
            else:
                verdict = "Uncertain"

        elif lower.startswith("confidence"):
            parts = stripped.split(":", 1)
            if len(parts) > 1:
                # Accept "0.87" or "87%" or "87"
                raw_val = parts[1].strip().replace("%", "")
                try:
                    val = float(raw_val)
                    confidence = val / 100 if val > 1 else val  # normalise %
                    confidence = max(0.0, min(1.0, confidence))  # clamp
                except ValueError:
                    pass

        elif lower.startswith("explanation"):
            parts = stripped.split(":", 1)
            if len(parts) > 1:
                explanation = parts[1].strip()

    return FactCheckResponse(
        claim=claim,
        verdict=verdict,
        confidence=confidence,
        explanation=explanation,
        sources=sources,
    )