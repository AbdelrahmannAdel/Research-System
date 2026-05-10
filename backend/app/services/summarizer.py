from google import genai
from fastapi import HTTPException
from app.core.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)

def summarize(text: str) -> str:
    prompt = f"""You are a research paper summarizer.
Read the following text from a research paper and write a single well-structured paragraph that summarizes the paper's main objective, methodology, and findings.
Be concise and academic in tone.

Text:
{text}"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"[summarizer] ERROR: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Summarization failed: {str(e)}"
        )