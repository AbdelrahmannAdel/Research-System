# AI-Based Research Paper Intelligence System

A senior capstone project that automatically classifies, summarizes, extracts keywords from, and recommends similar papers for any uploaded research paper PDF.

---

## Prerequisites

Install these before setting up the project:

- [Python 3.10](https://www.python.org/downloads/release/python-3100/) — check "Add Python to PATH" during install
- [Node.js LTS](https://nodejs.org/) — all defaults
- [Git](https://git-scm.com/download/win) — all defaults
- [PostgreSQL 16](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads) — set password to `pass`, port `5432`, install pgAdmin 4

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/YOURUSERNAME/research-system.git
cd research-system
```

### 2. Create the database

Open pgAdmin 4 → Servers → PostgreSQL 16 → enter password → right-click Databases → Create → Database → name: `researchdb` → Save

### 3. Backend

```bash
cd backend
py -3.10 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file inside `backend/` (get values from team lead):

```
DATABASE_URL=postgresql://postgres:pass@localhost:5432/researchdb
SECRET_KEY=same_secret_key_as_team_lead
```

### 4. Frontend

```bash
cd frontend
npm install
```

This installs all dependencies including React, Tailwind CSS, PostCSS, autoprefixer, React Router, and Axios.

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

## Daily Workflow

```bash
git pull
# make your changes
git add .
git commit -m "what you did"
git push
```

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
| Recommendations | arXiv API + Cosine Similarity |
