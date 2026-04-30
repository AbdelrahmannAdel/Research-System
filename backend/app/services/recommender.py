import requests
from sentence_transformers import SentenceTransformer, util

# load the embedding model once at module level so it isn't reloaded on every request
model = SentenceTransformer("all-MiniLM-L6-v2")

# fetch 20 candidate papers from Semantic Scholar using title and keywords
# then re-rank by cosine similarity and return top 10
def get_recommendations(title: str, keywords: list) -> list:

    # combine title and top 3 keywords into a single search query string
    query_terms = [title] + keywords[:3]
    query = " ".join(query_terms)

    # Semantic Scholar API endpoint
    url = "https://api.semanticscholar.org/graph/v1/paper/search"

    # fields specifies what data to return for each paper
    params = {
        "query": query,
        "limit": 20,
        "fields": "title,abstract,authors,externalIds,year"
    }

    # identify our application to reduce the chance of being rate-limited
    headers = {"User-Agent": "ResearchPaperSystem/1.0"}

    # make the API call, response is JSON
    response = requests.get(url, headers=headers, params=params, timeout=10)
    data = response.json()

    # build a clean list of candidates from the response
    candidates = []
    for paper in data.get("data", []):

        # skip papers with missing title or abstract, they can't be displayed or embedded
        if not paper.get("abstract") or not paper.get("title"):
            continue

        # build a URL for the paper, prefer arXiv link if available,
        # otherwise fall back to the Semantic Scholar page
        ext_ids = paper.get("externalIds", {})
        if ext_ids.get("ArXiv"):
            url_link = f"https://arxiv.org/abs/{ext_ids['ArXiv']}"
        else:
            url_link = f"https://www.semanticscholar.org/paper/{paper['paperId']}"

        candidates.append({
            "title": paper["title"],
            "abstract": paper["abstract"],
            "authors": ", ".join(
                a["name"] for a in paper.get("authors", [])
            ),
            "url": url_link
        })

    # if the API returned nothing useful, return empty list
    if not candidates:
        return []

    # embed the uploaded paper query (title + keywords) into a vector
    uploaded_embedding = model.encode(" ".join(query_terms), convert_to_tensor=True)

    # embed all candidate abstracts into vectors
    abstracts = [c["abstract"] for c in candidates]
    candidate_embeddings = model.encode(abstracts, convert_to_tensor=True)

    # compute cosine similarity between the uploaded paper and each candidate
    # scores[i] is a float between -1 and 1, where 1 means identical
    scores = util.cos_sim(uploaded_embedding, candidate_embeddings)[0]

    # attach similarity score to each candidate as a percentage (0-100)
    for i, candidate in enumerate(candidates):
        candidate["similarity"] = round(float(scores[i]) * 100)

    # sort by similarity descending, filter out weak matches, return top 10
    results = sorted(candidates, key=lambda x: x["similarity"], reverse=True)
    results = [r for r in results if r["similarity"] >= 30]

    return results[:10]