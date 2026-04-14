# Handles all paper-related endpoints: upload, recommend, save, and profile
# All routes here are prefixed with /papers (set in main.py)
# Upload and recommend use real AI services.
# Save and profile interact with the real database

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

# Request body model for /recommend
class RecommendRequest(BaseModel):
    title: str
    keywords: List[str]

# Request body model for /save
# recommendations is a list of dicts, each dict is one recommendation object
class SaveRequest(BaseModel):
    title: str
    main_category: str
    subcategory: str
    summary: str
    keywords: List[str]
    recommendations: List[dict]


@router.post("/upload")
async def upload_paper(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    # Read raw bytes from the uploaded PDF
    file_bytes = await file.read()

    # Extract title, full text, and summary input from the PDF
    extracted = extract_from_pdf(file_bytes)

    # Clean the full text for classifier and keyword extractor
    cleaned_text = clean_text(extracted["full_text"])

    # Run classification, summarization, and keyword extraction in parallel
    classification = classify(cleaned_text)
    summary = summarize(extracted["summary_input"])
    keywords = extract_keywords(cleaned_text)

    return {
        "title": extracted["title"],
        "main_category": classification["main_category"],
        "subcategory": classification["subcategory"],
        "summary": summary,
        "keywords": keywords,
        "confidence_score": classification["confidence_score"],
        "low_confidence": classification["low_confidence"]
    }


@router.post("/recommend")
def recommend_papers(request: RecommendRequest, current_user: User = Depends(get_current_user)):
    # Call the recommender service with title and keywords
    results = get_recommendations(request.title, request.keywords)
    return results


@router.post("/save")
def save_paper(request: SaveRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Convert keywords list to comma-separated string for VARCHAR storage
    keywords_str = ", ".join(request.keywords)

    # Convert recommendations list of dicts to JSON string for TEXT storage
    recommendations_str = json.dumps(request.recommendations)

    # Create a new SavedPaper row linked to the logged-in user
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
    # Fetch all saved papers belonging to the logged-in user
    papers = db.query(SavedPaper).filter(SavedPaper.user_id == current_user.id).all()

    # Convert each SQLAlchemy object to a dict the frontend can use
    # Also reverse the storage transformations: split keywords, parse recommendations JSON
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