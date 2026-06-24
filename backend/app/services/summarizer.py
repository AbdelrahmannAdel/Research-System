# Summarizes research paper text using Groq (primary) and Gemini (fallback).
# Takes cleaned text as input and returns a single academic paragraph
# covering the paper's objective, methodology, and findings.
#
# Provider priority:
#   1. Groq (llama-3.3-70b-versatile)
#   2. Gemini (gemini-2.5-flash)

from groq import Groq
import google.genai as genai
from fastapi import HTTPException
from app.core.config import settings

# Initialize both clients once at module load
groq_client = Groq(api_key=settings.GROQ_API_KEY)
gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)

# Shared prompt used by both providers
PROMPT_TEMPLATE = """You are a research paper summarizer.
Read the following text from a research paper and write a single well-structured paragraph that summarizes the paper's main objective, methodology, and findings.
Be concise and academic in tone.

Text:
{text}"""


def _summarize_with_groq(text: str) -> str:
    # Primary summarizer: Groq API running llama-3.3-70b-versatile
    # Free tier: 14,400 requests/day, 500,000 tokens/minute
    prompt = PROMPT_TEMPLATE.format(text=text)
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,   # low temperature for consistent academic tone
        max_tokens=512,    # enough for one well-structured paragraph
    )
    return response.choices[0].message.content.strip()


def _summarize_with_gemini(text: str) -> str:
    # Fallback summarizer: Google Gemini 2.5 Flash
    prompt = PROMPT_TEMPLATE.format(text=text)
    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text.strip()


def summarize(text: str) -> str:
    # Try Groq first
    try:
        print("[SUMMARIZER] Trying Groq ...")
        result = _summarize_with_groq(text)
        print("[SUMMARIZER] Groq succeeded.")
        return result
    except Exception as e:
        print(f"[SUMMARIZER] Groq failed: {type(e).__name__}: {e}")

    # Fall back to Gemini
    try:
        print("[SUMMARIZER] Falling back to Gemini ...")
        result = _summarize_with_gemini(text)
        print("[SUMMARIZER] Gemini succeeded.")
        return result
    except Exception as e:
        print(f"[SUMMARIZER] Gemini failed: {type(e).__name__}: {e}")

    # Both providers failed
    raise HTTPException(
        status_code=503,
        detail="Summarization failed: both Groq and Gemini are unavailable. Please try again."
    )