
# ResearchPilot — AI Based Research Paper Intelligence System
 
> Upload a research paper PDF. Get classification, summary, keywords, and ranked similar papers all in one pass.
 
**Live demo:** [researchpilot.tech](https://researchpilot.tech)
 
---
 
## What it does
 
ResearchPilot is a full-stack AI web application that analyzes any academic PDF and returns four structured outputs:
 
| Output | Method | Detail |
|---|---|---|
| **Hierarchical Classification** | Two fine-tuned SciBERT models | 7 main categories × 6 subcategories = 42 total |
| **Abstractive Summary** | Groq (Llama 3.3 70B) + Gemini fallback | Single academic-register paragraph |
| **Top Keywords** | YAKE (unsupervised) | Top 10 bigrams extracted from full text |
| **Similar Papers** | OpenAlex API + cosine re-ranking | 20 candidates → top 10 by semantic similarity |
 
Users can save analyses to a private personal library and revisit them without re-uploading.
 
---
 
## Classification Architecture
 
The classification pipeline uses a **hierarchical two-model design**:
 
```
PDF Text (title + abstract)
        │
        ▼
   ┌─────────┐
   │   L1    │  SciBERT fine-tuned on 7 main categories
   │  Model  │  → returns top-2 candidates with probabilities
   └─────────┘
        │
   ┌────┴────┐
   ▼         ▼
  [Cat A]  [Cat B]   For each candidate:
   │         │       prepend "Main category: {name}" hint
   ▼         ▼       run L2 with logit masking (6 allowed subcategories)
   ┌─────────┐
   │   L2    │  SciBERT fine-tuned on 42 subcategories
   │  Model  │  → masked softmax over 6 allowed subcategories only
   └─────────┘
        │
        ▼
  Combined Score = L1_prob × L2_prob
  Winner = highest combined score
        │
        ▼
  L2 confidence < 0.6 → graceful degradation ("Unclassified")
```

---
 
## Model Performance
 
Trained on **839,875 papers** (arXiv + PubMed + OpenAlex + UoB), ~20,000 per subcategory.
 
| Model | Accuracy | Weighted F1 |
|---|---|---|
| L1 — Main Category (7 classes) | **94.45%** | 0.9445 |
| L2 — Subcategory (42 classes) | **88.91%** | 0.8889 |
 
Train / Val / Test split: 80% / 10% / 10% (stratified on subcategory label).  
Base model: `allenai/scibert_scivocab_uncased` · Hardware: A100 GPU · Framework: HuggingFace Transformers
 
---
 
## Dataset
 
| Source | Papers | Categories covered |
|---|---|---|
| arXiv (Kaggle snapshot) | ~394,000 | Computer Science, Mathematics, Physics, Systems & Control |
| PubMed (NCBI baseline XML) | ~120,000 | Biology & Medicine (6 subcategories via MeSH scoring using k-means clustering) |
| OpenAlex API | ~340,000 | Chemistry, Engineering, Economics & Business |
| University of Bahrain papers | ~233 | Computer Science |
| **Total** | **~840,000** | **All 42 subcategories** |
 
---
 
## Tech Stack
 
| Layer | Technology |
|---|---|
| Frontend | React 19 + Vite + Tailwind CSS + React Router v7 |
| Backend | Python 3.10 + FastAPI + SQLAlchemy + Uvicorn |
| Database | PostgreSQL 16 |
| Auth | bcrypt + JWT (HS256, 24h expiry) |
| PDF Processing | PyMuPDF (fitz) |
| Classification | SciBERT (`allenai/scibert_scivocab_uncased`), fine-tuned × 2 |
| Summarization | Groq (Llama 3.3 70B) + Google Gemini 2.5 Flash fallback |
| Keywords | YAKE unsupervised, bigrams, top 10 |
| Embeddings | Sentence-Transformers (`all-MiniLM-L6-v2`) |
| Recommendations | OpenAlex API (250M+ works) + cosine similarity re-ranking |
| Deployment | Vercel (frontend) · Railway (backend) · HuggingFace (models) · Supabase (database)|
 
---
 
## Project Structure
 
```
Research-System/
├── frontend/                  # React 19 + Vite + Tailwind
│   └── src/
│       ├── pages/             # LoginPage, RegisterPage, HomePage, ProfilePage
│       ├── components/        # Navbar
│       └── styles/            # Ivory design system (CSS custom properties)
│
├── backend/
│   └── app/
│       ├── api/               # auth.py, papers.py (FastAPI routers)
│       ├── core/              # config.py, security.py, dependencies.py
│       ├── models/            # user.py, paper.py (SQLAlchemy ORM)
│       └── services/
│           ├── classifier.py       # L1 + L2 SciBERT inference pipeline
│           ├── summarizer.py       # Groq + Gemini fallback
│           ├── recommender.py      # OpenAlex + cosine re-ranking
│           ├── keyword_extractor.py
│           ├── pdf_extractor.py
│           └── preprocessor.py
│
└── backend/models/
    ├── scibert_l1/            # Fine-tuned L1 weights (hosted on HuggingFace)
    ├── scibert_l2/            # Fine-tuned L2 weights (hosted on HuggingFace)
    └── label_mappings/        # id2label / label2id JSON files
```
---
 
## Key Design Decisions
 
- **Why SciBERT over general BERT?** SciBERT was pre-trained on 1.14M scientific papers with a domain-specific vocabulary (`scivocab`), reducing OOV rates on scientific terminology significantly.
- **Why Top-K=2 for L1?** If L1's top prediction is wrong, the correct category is often the second-highest. K=2 catches these near-misses at the cost of one extra L2 forward pass (~1-2s).
- **Why OpenAlex over Semantic Scholar?** Semantic Scholar aggressively rate-limits anonymous requests. OpenAlex is free, requires no API key, and covers 250M+ works across all disciplines.
- **Why YAKE over KeyBERT?** YAKE is unsupervised and requires no corpus which is ideal for single-document keyword extraction. KeyBERT is ~10× slower for marginal quality gains on this task.
- **Why store recommendations as JSON TEXT?** Avoids a third database table for a read-heavy, rarely-queried field. Parsed back to a list on every profile read with `json.loads()`.
---
 
## Authors
 
University of Bahrain - Senior Project - 2026
 
- **Abdelrahman Adel** - Team Lead · Backend · AI pipeline · Dataset building · SciBERT training
- **Mohammed Al Jariri** - Backend
- **Mohammed Yaser Al Yusuf** - Frontend