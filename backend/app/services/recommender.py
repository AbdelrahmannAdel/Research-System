import requests
import time
from sentence_transformers import SentenceTransformer, util
from app.core.config import settings

_embedding_model = None
_cache = {}

def _get_embedding_model():
    # Lazy-load the embedding model once and reuse it across all requests
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model

def _make_cache_key(title: str, keywords: list) -> str:
    # Cache key is title + top 3 keywords (sorted for consistency regardless of order)
    # Prevents duplicate API calls if the same paper is re-fetched in the same session
    return f"{title}|||{' '.join(sorted(keywords[:3]))}"

def _try_semantic_scholar(query_terms: list) -> list | None:
    
    # Fetch recommendations from Semantic Scholar.
    # Retries up to 3 times with exponential backoff on 429 rate-limit responses.
    print("[RECOMMENDER] Trying Semantic Scholar ...")
    query = " ".join(query_terms)
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": 20,
        "fields": "title,abstract,authors,externalIds,year",
    }
    
    headers = {"User-Agent": "ResearchPaperSystem/1.0"}
    if settings.SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = settings.SEMANTIC_SCHOLAR_API_KEY

    max_retries = 1
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)

            if resp.status_code == 429:
                print(f"[RECOMMENDER] Semantic Scholar rate-limited (429). Moving to fallback ...")
                return None

            if resp.status_code != 200:
                print(f"[RECOMMENDER] Semantic Scholar returned {resp.status_code}")
                return None

            data = resp.json()
            papers = data.get("data", [])
            print(f"[RECOMMENDER] Semantic Scholar returned {len(papers)} papers")

            candidates = []
            for p in papers:
                # Skip papers with no abstract or title, they can't be ranked or displayed
                if not p.get("abstract") or not p.get("title"):
                    continue
                
                # Prefer arXiv link if available, otherwise use Semantic Scholar paper page
                ext_ids = p.get("externalIds", {})
                link = (
                    f"https://arxiv.org/abs/{ext_ids['ArXiv']}"
                    if ext_ids.get("ArXiv")
                    else f"https://www.semanticscholar.org/paper/{p.get('paperId', '')}"
                )
                candidates.append({
                    "source": "Semantic Scholar",
                    "title": p["title"],
                    "abstract": p["abstract"],
                    "authors": ", ".join(a["name"] for a in p.get("authors", [])),
                    "url": link,
                })

            if not candidates:
                return None

            results = _rank_candidates(candidates, query_terms, min_similarity=30.0)
            return results if results else None

        except Exception as exc:
            print(f"[RECOMMENDER] Semantic Scholar error (attempt {attempt + 1}): {exc}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

    print("[RECOMMENDER] Semantic Scholar failed after all retries.")
    return None


def _try_core(query_terms: list) -> list | None:
    
    # Fetch recommendations from CORE API v3 (fallback).
    print("[RECOMMENDER] Falling back to CORE API ...")
    query = " ".join(query_terms)

    url = "https://api.core.ac.uk/v3/search/works"
    params = {
        "q": query,
        "limit": 20,
    }
    headers = {
        "Authorization": f"Bearer {settings.CORE_API_KEY}"
    }
    
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=20)
        if resp.status_code != 200:
            print(f"[RECOMMENDER] CORE returned {resp.status_code}: {resp.text[:200]}")
            print(f"[RECOMMENDER] CORE rate limit remaining: {resp.headers.get('x-ratelimit-remaining', 'unknown')}")
            return None

        data = resp.json()
        papers = data.get("results", [])
        print(f"[RECOMMENDER] CORE returned {len(papers)} papers")

        candidates = []
        for p in papers:
            title = p.get("title")
            abstract = p.get("abstract")
            
            # Skip papers missing title or abstract, unusable for ranking or display
            if not title or not abstract:
                continue

            authors_list = p.get("authors", [])
            author_str = (
                ", ".join(a.get("name", "") for a in authors_list)
                if authors_list
                else "Unknown"
            )

            link = p.get("downloadUrl", "https://core.ac.uk")
            if isinstance(link, list):
                link = link[0] if link else "https://core.ac.uk"

            candidates.append({
                "source": "CORE",
                "title": title,
                "abstract": abstract.strip(),
                "authors": author_str,
                "url": link,
            })

        if not candidates:
            return None

        # min_similarity=0.0 — rank but do not filter out any results
        return _rank_candidates(candidates, query_terms, min_similarity=0.0)

    except Exception as exc:
        print(f"[RECOMMENDER] CORE error: {exc}")
        return None


def _rank_candidates(candidates: list, query_terms: list, min_similarity: float = 30.0) -> list:
    # Embed query + abstracts, compute cosine similarity, optionally filter, sort descending, return top 10.

    # Pass min_similarity=0.0 to skip filtering (used for CORE fallback so that
    # any real paper is returned rather than falling through to mock data).
    model = _get_embedding_model()
    query_str = " ".join(query_terms)

    uploaded_emb = model.encode(query_str, convert_to_tensor=True)
    abstract_texts = [c["abstract"] for c in candidates]
    candidate_embs = model.encode(abstract_texts, convert_to_tensor=True)
    scores = util.cos_sim(uploaded_emb, candidate_embs)[0]

    for i, c in enumerate(candidates):
        c["similarity"] = round(float(scores[i]) * 100)

    if min_similarity > 0:
        candidates = [c for c in candidates if c["similarity"] >= min_similarity]

    candidates.sort(key=lambda x: x["similarity"], reverse=True)
    return candidates[:10]

def get_recommendations(title: str, keywords: list) -> list:
    
    # Check cache first to avoid redundant API calls for the same paper in one session
    cache_key = _make_cache_key(title, keywords)
    if cache_key in _cache:
        print("[RECOMMENDER] Cache HIT")
        return _cache[cache_key]

    # Query is title + top 3 keywords for best search relevance
    query_terms = [title] + keywords[:3]

    # Lazy-load embedding model once
    _get_embedding_model()

    # 1. Try Semantic Scholar (with retry on 429)
    results = _try_semantic_scholar(query_terms)

    # 2. Fall back to CORE
    if not results:
        results = _try_core(query_terms)

    # 3. Last-resort mock
    if not results:
        print("[RECOMMENDER] WARNING: All providers failed — returning empty list")
        results = []

    _cache[cache_key] = results
    return results