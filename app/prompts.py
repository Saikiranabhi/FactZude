FACT_CHECK_PROMPT = """
You are an AI fact-checking system.

Claim:
{claim}

Web Evidence:
{evidence}

Return:
- Verdict (True/False/Uncertain)
- Confidence Score (0-1)
- Short Explanation
"""