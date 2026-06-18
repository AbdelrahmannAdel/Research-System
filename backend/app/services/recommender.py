import requests
import time
from sentence_transformers import SentenceTransformer, util

# No settings import needed — OpenAlex requires no API key

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


def _reconstruct_abstract(inverted_index: dict) -> str:
    # OpenAlex stores abstracts as an inverted index: { "word": [position, position, ...], ... }
    # We reconstruct the original text by sorting all (position, word) pairs and joining them
    if not inverted_index:
        return ""
    word_positions = [
        (pos, word)
        for word, positions in inverted_index.items()
        for pos in positions
    ]
    word_positions.sort(key=lambda x: x[0])
    return " ".join(word for _, word in word_positions)


def _try_openalex(query_terms: list) -> list | None:
    # Fetch recommendation candidates from OpenAlex.
    # OpenAlex is free, requires no API key, and has 250M+ works.
    # We pass a mailto param as a courtesy to OpenAlex to identify our app
    # and get access to the "polite pool" (faster, more reliable responses).
    print("[RECOMMENDER] Trying OpenAlex ...")

    query = " ".join(query_terms)

    url = "https://api.openalex.org/works"
    params = {
        "search": query,
        "per_page": 20,
        # Request only the fields we need to keep the response small and fast
        "select": "title,abstract_inverted_index,authorships,id,doi",
        # Polite pool: identifies our app to OpenAlex for better rate limits
        "mailto": "researchpilot@university.edu",
    }

    try:
        resp = requests.get(url, params=params, timeout=15)

        if resp.status_code != 200:
            print(f"[RECOMMENDER] OpenAlex returned {resp.status_code}")
            return None

        data = resp.json()
        works = data.get("results", [])
        print(f"[RECOMMENDER] OpenAlex returned {len(works)} works")

        candidates = []
        for w in works:
            title = w.get("title")

            # Reconstruct abstract from OpenAlex inverted index format
            abstract = _reconstruct_abstract(w.get("abstract_inverted_index"))

            # Skip papers missing title or abstract — unusable for ranking or display
            if not title or not abstract:
                continue

            # Build author string from authorships list
            authorships = w.get("authorships", [])
            authors = ", ".join(
                a.get("author", {}).get("display_name", "")
                for a in authorships[:5]  # cap at 5 authors to avoid very long strings
                if a.get("author", {}).get("display_name")
            ) or "Unknown"

            # Prefer DOI link if available, otherwise fall back to OpenAlex page
            doi = w.get("doi")
            openalex_id = w.get("id", "")  # e.g. "https://openalex.org/W12345"
            link = doi if doi else openalex_id

            candidates.append({
                "source": "OpenAlex",
                "title": title,
                "abstract": abstract.strip(),
                "authors": authors,
                "url": link,
            })

        if not candidates:
            print("[RECOMMENDER] OpenAlex returned no usable candidates")
            return None

        # Re-rank by cosine similarity, filter to >= 30% similarity
        results = _rank_candidates(candidates, query_terms, min_similarity=30.0)
        return results if results else None

    except Exception as exc:
        print(f"[RECOMMENDER] OpenAlex error: {exc}")
        return None


def _rank_candidates(candidates: list, query_terms: list, min_similarity: float = 30.0) -> list:
    # Embed query + candidate abstracts, compute cosine similarity,
    # filter by min_similarity, sort descending, return top 10.
    model = _get_embedding_model()
    query_str = " ".join(query_terms)

    # Encode the query and all abstracts in one batch for efficiency
    uploaded_emb = model.encode(query_str, convert_to_tensor=True)
    abstract_texts = [c["abstract"] for c in candidates]
    candidate_embs = model.encode(abstract_texts, convert_to_tensor=True)

    # Cosine similarity: shape (1, N) -> take first row
    scores = util.cos_sim(uploaded_emb, candidate_embs)[0]

    # Attach similarity score to each candidate (stored as integer percentage, e.g. 87)
    for i, c in enumerate(candidates):
        c["similarity"] = round(float(scores[i]) * 100)

    # Filter out candidates below the similarity threshold
    if min_similarity > 0:
        candidates = [c for c in candidates if c["similarity"] >= min_similarity]

    # Sort by similarity descending and return top 10
    candidates.sort(key=lambda x: x["similarity"], reverse=True)
    return candidates[:10]


def get_recommendations(title: str, keywords: list) -> list:
    # Public entry point called by papers.py /recommend endpoint.
    # Returns up to 10 semantically similar papers ranked by cosine similarity.

    # Check cache first to avoid redundant API calls for the same paper in one session
    cache_key = _make_cache_key(title, keywords)
    if cache_key in _cache:
        print("[RECOMMENDER] Cache HIT")
        return _cache[cache_key]

    # Query = title + top 3 keywords for best search relevance
    query_terms = [title] + keywords[:3]

    # Ensure embedding model is loaded before making API calls
    _get_embedding_model()

    # Try OpenAlex (free, no API key, 250M+ works)
    results = _try_openalex(query_terms)

    # If OpenAlex returns nothing (network error or no matches above threshold)
    if not results:
        print("[RECOMMENDER] WARNING: OpenAlex returned no results — returning empty list")
        results = []

    _cache[cache_key] = results
    return results
