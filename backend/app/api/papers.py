# Handles all paper-related endpoints: upload, recommend, save, and profile
# All routes here are prefixed with /papers (set in main.py)
# Upload and recommend use real AI services.
# Save and profile interact with the real database
import re
import unicodedata
import json
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User
from app.models.paper import SavedPaper
from app.core.dependencies import get_current_user
from app.services.pdf_extractor import extract_from_pdf
from app.services.preprocessor import clean_text
from app.services.classifier import classify
from app.services.summarizer import summarize
from app.services.keyword_extractor import extract_keywords
from app.services.recommender import get_recommendations

router = APIRouter()

class RecommendRequest(BaseModel):
    title: str
    keywords: List[str]

class SaveRequest(BaseModel):
    title: str
    main_category: str
    subcategory: str
    summary: str
    keywords: List[str]
    recommendations: List[dict]


@router.post("/upload")
async def upload_paper(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    file_bytes = await file.read()
    extracted = extract_from_pdf(file_bytes)

    abstract = extracted["abstract"] or extracted["intro"] or extracted["summary_input"]

    # normalize unicode from PDF (curly quotes, em dashes, ligatures, etc.)
    abstract = unicodedata.normalize("NFKC", abstract)
    # rejoin hyphenated line breaks (fo-\ncused → focused)
    abstract = re.sub(r"-\n", "", abstract)
    # collapse remaining newlines to spaces
    abstract = re.sub(r"\n", " ", abstract)

    title = unicodedata.normalize("NFKC", extracted["title"] or "")

    # do NOT apply clean_text() here — model was trained on raw text
    classify_input = title + "\n\n" + abstract

    # clean_text() only for keyword extraction
    cleaned_full_text = clean_text(extracted["full_text"])

    print(f"[CLASSIFY] Input length: {len(classify_input)} chars")
    print(f"[CLASSIFY] Abstract found: {bool(extracted['abstract'])}")
    print(f"[CLASSIFY] Preview: {classify_input[:300]}")
    print(f"[CLASSIFY] Abstract content: {repr(extracted['abstract'][:200])}")

    classification = classify(classify_input)
    print(f"[RESULT] {classification}")
    summary = summarize(extracted["summary_input"])
    keywords = extract_keywords(cleaned_full_text)

    return {
        "title": extracted["title"],
        "main_category": classification["main_category"],
        "subcategory": classification["subcategory"],
        "summary": summary,
        "keywords": keywords,
        "l1_confidence": classification["l1_confidence"],
        "l2_confidence": classification["l2_confidence"],
        "low_confidence": classification["low_confidence"]
    }


@router.post("/recommend")
def recommend_papers(request: RecommendRequest, current_user: User = Depends(get_current_user)):
    results = get_recommendations(request.title, request.keywords)
    return results


@router.post("/save")
def save_paper(request: SaveRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    keywords_str = ", ".join(request.keywords)
    recommendations_str = json.dumps(request.recommendations)

    new_paper = SavedPaper(
        user_id=current_user.id,
        title=request.title,
        main_category=request.main_category,
        subcategory=request.subcategory,
        summary=request.summary,
        keywords=keywords_str,
        recommendations=recommendations_str
    )

    db.add(new_paper)
    db.commit()
    db.refresh(new_paper)

    return {"message": "Paper saved successfully"}


@router.get("/profile")
def get_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    papers = db.query(SavedPaper).filter(SavedPaper.user_id == current_user.id).all()

    result = []
    for paper in papers:
        result.append({
            "id": paper.id,
            "title": paper.title,
            "main_category": paper.main_category,
            "subcategory": paper.subcategory,
            "summary": paper.summary,
            "keywords": paper.keywords.split(", "),
            "recommendations": json.loads(paper.recommendations),
            "saved_at": paper.saved_at.strftime("%Y-%m-%d") if paper.saved_at else None
        })

    return result