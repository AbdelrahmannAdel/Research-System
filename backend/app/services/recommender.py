import requests
from sentence_transformers import SentenceTransformer, util
import xml.etree.ElementTree as ET

# load the embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# fetch 20 candidate papers from arXiv using title and keywords
# then re-rank by cosine similarity and return top 10
def get_recommendations(title: str, keywords: list) -> list:
        
    #combine title and top 3 keywords into a search query
    query_terms = [title] + keywords[:3]
    query = " ".join(query_terms)
    
    # call the arXiv API, returns Atom XML with metadata
    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": 20
    }
    response = requests.get(url, params=params, timeout=10)
    
    # parse the XML response
    root = ET.fromstring(response.text)
    namespace = {"atom": "http://www.w3.org/2005/Atom"}

    # extract title, abstract, authors, and URL from each result
    candidates = []
    for entry in root.findall("atom:entry", namespace):
        candidates.append({
            "title": entry.find("atom:title", namespace).text.strip(),
            "abstract": entry.find("atom:summary", namespace).text.strip(),
            "authors": ", ".join(
                author.find("atom:name", namespace).text
                for author in entry.findall("atom:author", namespace)
            ),
            "url": entry.find("atom:id", namespace).text.strip()
        })
    
    # if arXiv returned nothing, return empty list
    if not candidates:
        return []
    
    # embed the uploaded paper (title + keywords combined)
    uploaded_embedding = model.encode(" ".join(query_terms), convert_to_tensor=True)

    # embed all candidate abstracts
    abstracts = [c["abstract"] for c in candidates]
    candidate_embeddings = model.encode(abstracts, convert_to_tensor=True)

    # compute cosine similarity between uploaded paper and each candidate
    scores = util.cos_sim(uploaded_embedding, candidate_embeddings)[0]
    
    # attach similarity scores to each candidate
    for i, candidate in enumerate(candidates):
        candidate["similarity"] = round(float(scores[i]) * 100)
        
    # filter out low similarity results, sort by score, return top 10
    results = sorted(candidates, key=lambda x: x["similarity"], reverse=True)
    results = [r for r in results if r["similarity"] >= 30]

    return results[:10]
