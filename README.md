# AI-Based Research Paper Classifier and Summarizer
# Research Pilot

A senior project that automatically classifies, summarizes, extracts keywords from, and recommends similar papers for any uploaded research paper PDF
---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Tailwind CSS + Axios + React Router |
| Backend | Python + FastAPI + SQLAlchemy |
| Auth | bcrypt + JWT (python-jose) |
| Database | PostgreSQL |
| PDF Processing | PyMuPDF |
| Classification | SciBERT (fine-tuned, 2 models) |
| Summarization | Google Gemini API |
| Keywords | YAKE |
| Embeddings | Sentence-Transformers (all-MiniLM-L6-v2) |
| Recommendations | semantic scholar API + Cosine Similarity |
