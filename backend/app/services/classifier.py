# TO BE REPLACED WITH REAL SciBERT INFERENCE

# takes cleaned full text of the paper
# returns main_category, subcategory, confidence_score, and low_confidence flag
def classify(text: str) -> dict:
    
    confidence_score = 0.91

    return {
        "main_category": "Computer Science",
        "subcategory": "Machine Learning",
        "confidence_score": confidence_score,
        "low_confidence": confidence_score < 0.6  # warn frontend if below 60% confidence
    }