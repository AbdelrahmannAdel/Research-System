# TO BE REPLACED WITH REAL SciBERT INFERENCE

# takes cleaned full text of the paper
# returns main_category, subcategory, l1_confidence, l2_confidence, and low_confidence flag
def classify(text: str) -> dict:
    
    l1_confidence = 0.91
    l2_confidence = 0.91
    
    return {
        "main_category": "Computer Science",
        "subcategory": "Machine Learning",
        "l1_confidence": l1_confidence,
        "l2_confidence": l2_confidence,
        "low_confidence": l2_confidence < 0.6
    }