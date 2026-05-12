# AI-Based Research Paper Classifier and Summarizer
# Research Pilot

A senior project that automatically classifies, summarizes, extracts keywords from, and recommends similar papers for any uploaded research paper PDF

---

## Prerequisites

Install these before setting up the project:

- [Python 3.10](https://www.python.org/downloads/release/python-3100/)
- [Node.js LTS](https://nodejs.org/) — all defaults
- [Git](https://git-scm.com/download/win) — all defaults
- [PostgreSQL 16](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads)
---

## Running the Project

**Backend** (in a terminal with venv active):

```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

Runs at http://localhost:8000 — API docs at http://localhost:8000/docs

**Frontend** (in a separate terminal):

```bash
cd frontend
npm run dev
```

Runs at http://localhost:5173
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
