import google.generativeai as genai
from app.core.config import settings

# configure gemini with our API key from .env
genai.configure(api_key=settings.GEMINI_API_KEY)

# use gemini 2.0 flash
model = genai.GenerativeModel("gemini-2.0-flash")

# send text to gemini and return a 4-5 sentence summary of the research
def summarize(text: str) -> str:
    prompt = f"""You are a research paper summarizer.
Read the following text from a research paper and write a single well-structured paragraph that summarizes the paper's main objective, methodology, and findings.
Be concise and academic in tone.

Text:
{text}"""
    
    # API call
    response = model.generate_content(prompt)
    
    return response.text
