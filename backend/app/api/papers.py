# Handles all paper-related endpoints: upload, recommend, save, and profile
# All routes here are prefixed with /papers (set in main.py)
# Upload and recommend return hardcoded mock data (real AI logic added in Phase 3)
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
def upload_paper(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    # File is received but ignored — mock response returned instead
    # In Phase 3 this will run the full AI pipeline: extract, classify, summarize, keywords
    return {
        "title": "Attention Is All You Need",
        "main_category": "Computer Science",
        "subcategory": "Machine Learning",
        "summary": "This paper proposes the Transformer, a novel neural network architecture based entirely on attention mechanisms, dispensing with recurrence and convolutions. The model achieves state-of-the-art results on machine translation tasks while being significantly more parallelizable and requiring substantially less training time.",
        "keywords": ["transformer", "attention mechanism", "neural network", "machine translation", "self-attention"],
        "confidence_score": 0.94,
        "low_confidence": False
    }


@router.post("/recommend")
def recommend_papers(request: RecommendRequest, current_user: User = Depends(get_current_user)):
    # Title and keywords are received but ignored — mock recommendations returned instead
    # In Phase 3 this will call the arXiv API and re-rank results using cosine similarity
    return [
        {
            "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
            "authors": "Devlin et al.",
            "abstract": "We introduce BERT, a new language representation model designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers.",
            "similarity": 94,
            "url": "https://arxiv.org/abs/1810.04805"
        },
        {
            "title": "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale",
            "authors": "Dosovitskiy et al.",
            "abstract": "While the Transformer architecture has become the de-facto standard for NLP tasks, its applications to computer vision remain limited. We show that a pure transformer applied directly to sequences of image patches can perform very well on image classification tasks.",
            "similarity": 88,
            "url": "https://arxiv.org/abs/2010.11929"
        },
        {
            "title": "GPT-3: Language Models are Few-Shot Learners",
            "authors": "Brown et al.",
            "abstract": "We demonstrate that scaling language models greatly improves task-agnostic, few-shot performance, sometimes even becoming competitive with prior state-of-the-art fine-tuning approaches.",
            "similarity": 85,
            "url": "https://arxiv.org/abs/2005.14165"
        },
        {
            "title": "Scaling Laws for Neural Language Models",
            "authors": "Kaplan et al.",
            "abstract": "We study empirical scaling laws for language model performance on the cross-entropy loss. The loss scales as a power-law with model size, dataset size, and the amount of compute used for training.",
            "similarity": 79,
            "url": "https://arxiv.org/abs/2001.08361"
        },
        {
            "title": "Deep Residual Learning for Image Recognition",
            "authors": "He et al.",
            "abstract": "We present a residual learning framework to ease the training of networks that are substantially deeper than those used previously. We explicitly reformulate the layers as learning residual functions with reference to the layer inputs.",
            "similarity": 72,
            "url": "https://arxiv.org/abs/1512.03385"
        },
        {
            "title": "Generative Adversarial Networks",
            "authors": "Goodfellow et al.",
            "abstract": "We propose a new framework for estimating generative models via an adversarial process, in which we simultaneously train two models: a generative model G that captures the data distribution, and a discriminative model D.",
            "similarity": 68,
            "url": "https://arxiv.org/abs/1406.2661"
        },
        {
            "title": "Dropout: A Simple Way to Prevent Neural Networks from Overfitting",
            "authors": "Srivastava et al.",
            "abstract": "We describe dropout, a technique for addressing overfitting in neural networks. The key idea is to randomly drop units from the neural network during training.",
            "similarity": 64,
            "url": "https://jmlr.org/papers/v15/srivastava14a.html"
        },
        {
            "title": "Adam: A Method for Stochastic Optimization",
            "authors": "Kingma and Ba",
            "abstract": "We introduce Adam, an algorithm for first-order gradient-based optimization of stochastic objective functions, based on adaptive estimates of lower-order moments.",
            "similarity": 61,
            "url": "https://arxiv.org/abs/1412.6980"
        },
        {
            "title": "XLNet: Generalized Autoregressive Pretraining for Language Understanding",
            "authors": "Yang et al.",
            "abstract": "With the capability of modeling bidirectional contexts, denoising autoencoding based pretraining like BERT achieves better performance than pretraining approaches based on autoregressive language modeling.",
            "similarity": 57,
            "url": "https://arxiv.org/abs/1906.08237"
        },
        {
            "title": "RoBERTa: A Robustly Optimized BERT Pretraining Approach",
            "authors": "Liu et al.",
            "abstract": "We present a replication study of BERT pretraining that carefully measures the impact of many key hyperparameters and training data size. We find that BERT was significantly undertrained.",
            "similarity": 53,
            "url": "https://arxiv.org/abs/1907.11692"
        }
    ]


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