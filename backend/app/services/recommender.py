import requests
import time
import urllib.parse
from sentence_transformers import SentenceTransformer, util
from app.core.config import settings

_embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
_cache = {}

def _make_cache_key(title: str, keywords: list) -> str:
    return f"{title}|||{' '.join(sorted(keywords[:3]))}"

def _try_semantic_scholar(query_terms: list) -> list | None:
    """Attempt to fetch recommendations from Semantic Scholar."""
    print("[RECOMMENDER] Trying Semantic Scholar ...")
    query = " ".join(query_terms)
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": 20,
        "fields": "title,abstract,authors,externalIds,year",
    }
    headers = {"User-Agent": "ResearchPaperSystem/1.0"}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code != 200:
            print(f"[RECOMMENDER] Semantic Scholar returned {resp.status_code}")
            return None

        data = resp.json()
        papers = data.get("data", [])
        print(f"[RECOMMENDER] Semantic Scholar returned {len(papers)} papers")

        candidates = []
        for p in papers:
            if not p.get("abstract") or not p.get("title"):
                continue
            ext_ids = p.get("externalIds", {})
            link = (
                f"https://arxiv.org/abs/{ext_ids['ArXiv']}"
                if ext_ids.get("ArXiv")
                else f"https://www.semanticscholar.org/paper/{p.get('paperId', '')}"
            )
            candidates.append(
                {
                    "title": p["title"],
                    "abstract": p["abstract"],
                    "authors": ", ".join(a["name"] for a in p.get("authors", [])),
                    "url": link,
                }
            )

        if not candidates:
            return None

        # Embed and compute similarity
        uploaded_emb = _embedding_model.encode(
            " ".join(query_terms), convert_to_tensor=True
        )
        abstract_texts = [c["abstract"] for c in candidates]
        candidate_embs = _embedding_model.encode(
            abstract_texts, convert_to_tensor=True
        )
        scores = util.cos_sim(uploaded_emb, candidate_embs)[0]
        for i, c in enumerate(candidates):
            c["similarity"] = round(float(scores[i]) * 100)

        candidates = [c for c in candidates if c["similarity"] >= 30]
        candidates.sort(key=lambda x: x["similarity"], reverse=True)
        return candidates[:10]

    except Exception as exc:
        print(f"[RECOMMENDER] Semantic Scholar error: {exc}")
        return None

def _try_core(query_terms: list) -> list | None:
    """Attempt to fetch recommendations from CORE API v3."""
    print("[RECOMMENDER] Falling back to CORE API ...")
    query = " ".join(query_terms)
    encoded_query = urllib.parse.quote(query)

    # CORE API v3 Search Works endpoint
    url = "https://api.core.ac.uk/v3/search/works"
    params = {
        "q": encoded_query,
        "limit": 20,
        "fields": "title,abstract,authors,downloadUrl"
    }
    headers = {
        "Authorization": f"Bearer {settings.CORE_API_KEY}"
    }

    try:
        time.sleep(1)  # stay polite
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        if resp.status_code != 200:
            print(f"[RECOMMENDER] CORE returned {resp.status_code}: {resp.text}")
            return None

        data = resp.json()
        papers = data.get("results", [])
        print(f"[RECOMMENDER] CORE returned {len(papers)} papers")

        candidates = []
        for p in papers:
            title = p.get("title")
            abstract = p.get("abstract")
            if not title or not abstract:
                continue

            authors_list = p.get("authors", [])
            author_str = ", ".join(a.get("name", "") for a in authors_list) if authors_list else "Unknown"

            link = p.get("downloadUrl", "https://core.ac.uk")
            if isinstance(link, list):
                link = link[0] if link else "https://core.ac.uk"

            candidates.append(
                {
                    "title": title,
                    "abstract": abstract.strip(),
                    "authors": author_str,
                    "url": link,
                }
            )

        if not candidates:
            return None

        uploaded_emb = _embedding_model.encode(
            " ".join(query_terms), convert_to_tensor=True
        )
        abstract_texts = [c["abstract"] for c in candidates]
        candidate_embs = _embedding_model.encode(
            abstract_texts, convert_to_tensor=True
        )
        scores = util.cos_sim(uploaded_emb, candidate_embs)[0]
        for i, c in enumerate(candidates):
            c["similarity"] = round(float(scores[i]) * 100)

        candidates = [c for c in candidates if c["similarity"] >= 30]
        candidates.sort(key=lambda x: x["similarity"], reverse=True)
        return candidates[:10]

    except Exception as exc:
        print(f"[RECOMMENDER] CORE error: {exc}")
        return None

def _generate_mock_recommendations(title: str, keywords: list) -> list:
    """Last-resort fallback if all providers fail."""
    topic = keywords[0] if keywords else title.split()[-1]
    templates = [
        f"A Comprehensive Survey of {topic}",
        f"Recent Advances in {topic}",
        f"Foundations of {topic}",
        f"Deep Learning Approaches for {topic}",
        f"Theoretical Perspectives on {topic}",
        f"Practical Applications of {topic}",
        f"Challenges and Opportunities in {topic}",
        f"State-of-the-Art {topic} Methods",
        f"A Review of {topic} Research",
        f"Key Developments in {topic}",
    ]
    mock = []
    for i in range(10):
        mock.append(
            {
                "title": templates[i],
                "abstract": f"Mock abstract for testing {topic}.",
                "authors": "A. Author, B. Researcher",
                "url": "https://semanticscholar.org/mock",
                "similarity": round(90 - i * 8, 1),
            }
        )
    print("[RECOMMENDER] All providers failed — using mock data")
    return mock

def get_recommendations(title: str, keywords: list) -> list:
    cache_key = _make_cache_key(title, keywords)
    if cache_key in _cache:
        print("[RECOMMENDER] Cache HIT")
        return _cache[cache_key]

    query_terms = [title] + keywords[:3]

    # 1. Try Semantic Scholar
    results = _try_semantic_scholar(query_terms)

    # 2. Fall back to CORE
    if results is None:
        results = _try_core(query_terms)

    # 3. Last-resort mock
    if results is None:
        results = _generate_mock_recommendations(title, keywords)

    _cache[cache_key] = results
    return results