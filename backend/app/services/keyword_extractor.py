import yake

# extract the top 10 keywords from the cleaned paper text using YAKE
# returns a list of keyword strings

def extract_keywords(text: str) -> list:
    # Configure YAKE:
    # lan="en"        — English text
    # n=2             — extract up to 2-word phrases (e.g. "neural network" not just "neural")
    # dedupLim=0.7    — avoid returning very similar keywords (70% similarity threshold)
    # top=10          — return only the top 10 keywords
    extractor = yake.KeywordExtractor(lan="en", n=2, dedupLim=0.7, top=10)
    
    # extract_keywords returns a list of (keyword, score tuples)
    # we only want the keyword string
    results = extractor.extract_keywords(text)
    keywords = [kw for kw, score in results]

    return keywords