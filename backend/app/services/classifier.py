import json
import torch
import numpy as np
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Paths
BASE_MODEL_DIR = Path(__file__).parent.parent.parent / "models"

L1_MODEL_PATH = BASE_MODEL_DIR / "scibert_l1"
L2_MODEL_PATH = BASE_MODEL_DIR / "scibert_l2"
LABEL_MAPPINGS_PATH = BASE_MODEL_DIR / "label_mappings"

# Load label mappings (id -> label) once at module import
# (actually loaded when the module is first imported, but we'll also
# provide a function to load models later to keep lifespan clean)
def _load_label_mappings():
    with open(LABEL_MAPPINGS_PATH / "main_id2label.json", "r") as f:
        id2main = json.load(f)          # keys: "0", "1", ...
    with open(LABEL_MAPPINGS_PATH / "sub_id2label.json", "r") as f:
        id2sub = json.load(f)
    # Convert string keys to int for easier indexing
    id2main = {int(k): v for k, v in id2main.items()}
    id2sub = {int(k): v for k, v in id2sub.items()}
    return id2main, id2sub

ID2MAIN, ID2SUB = _load_label_mappings()
NUM_MAIN = len(ID2MAIN)     # 7
NUM_SUB = len(ID2SUB)       # 42

# Mappings from main category name to the set of allowed subcategory ids
# (6 subcategories per main category). We'll build this from the
# sub_label2id.json file (we need to know which sub belongs to which main).
# However, the current label_mappings/ only contain id2label, not the reverse
# mapping from main to sub ids. We'll define it explicitly based on the taxonomy.
# This ensures correct masking regardless of ordering.

# Taxonomy: main category -> list of subcategory names (exactly 6 each)
MAIN_TO_SUBS = {
    "Computer Science": [
        "Data Structures & Algorithms", "Machine Learning",
        "Natural Language Processing", "Robotics",
        "Cryptography & Security", "Artificial Intelligence"
    ],
    "Mathematics": [
        "Analysis", "Combinatorics", "Probability", "Algebra",
        "Numerical Analysis", "Optimization & Control"
    ],
    "Physics": [
        "Quantum Physics", "Astrophysics", "Condensed Matter",
        "High Energy Physics", "Relativity & Gravity", "Mathematical Physics"
    ],
    "Biology & Medicine": [
        "Neuroscience", "Genetics & Molecular Biology",
        "Immunology & Microbiology", "Oncology",
        "Cardiology", "Pharmacology"
    ],
    "Economics & Business": [
        "Econometrics", "Finance", "Marketing", "Management",
        "Accounting", "Management Information Systems"
    ],
    "Engineering": [
        "Electrical & Electronic Engineering", "Systems & Control",
        "Civil & Structural Engineering", "Mechanical Engineering",
        "Chemical Engineering", "Industrial & Manufacturing Engineering"
    ],
    "Chemistry": [
        "Organic Chemistry", "Inorganic Chemistry", "Analytical Chemistry",
        "Physical and Theoretical Chemistry", "Spectroscopy", "Electrochemistry"
    ]
}

# Build reverse mapping: subcategory name -> main category name
SUB_TO_MAIN = {}
for main, subs in MAIN_TO_SUBS.items():
    for sub in subs:
        SUB_TO_MAIN[sub] = main

# For each main category id (0..6), precompute the list of allowed subcategory ids
# We need id2sub map from label id to sub name, and then map name to id via
# a reverse dictionary built from id2sub.
SUB_NAME_TO_ID = {name: idx for idx, name in ID2SUB.items()}

ALLOWED_SUB_IDS = {}
for main_id, main_name in ID2MAIN.items():
    sub_names = MAIN_TO_SUBS.get(main_name, [])
    allowed_ids = [SUB_NAME_TO_ID[name] for name in sub_names if name in SUB_NAME_TO_ID]
    # Sanity check: should be exactly 6
    if len(allowed_ids) != 6:
        raise ValueError(f"Main {main_name} has {len(allowed_ids)} subcategories, expected 6")
    ALLOWED_SUB_IDS[main_id] = set(allowed_ids)

# Model loading (to be called from main.py lifespan event)
def load_models(device=None):
    
    # Load tokenizer and both SciBERT models.
    # Returns (l1_model, l2_model, tokenizer, device)
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    print(f"Loading tokenizer from {L1_MODEL_PATH}...")
    tokenizer = AutoTokenizer.from_pretrained(str(L1_MODEL_PATH))
    
    print(f"Loading L1 model from {L1_MODEL_PATH}...")
    l1_model = AutoModelForSequenceClassification.from_pretrained(str(L1_MODEL_PATH))
    l1_model.to(device)
    l1_model.eval()
    
    print(f"Loading L2 model from {L2_MODEL_PATH}...")
    l2_model = AutoModelForSequenceClassification.from_pretrained(str(L2_MODEL_PATH))
    l2_model.to(device)
    l2_model.eval()
    
    print(f"Models loaded on {device}")
    return l1_model, l2_model, tokenizer, device

# Inference functions
def softmax(logits):
    # Convert logits to probabilities
    exp = np.exp(logits - np.max(logits))
    return exp / np.sum(exp)

def get_top_k(probs, k=2):
    # Return indices and probabilities of top k entries
    indices = np.argsort(probs)[::-1][:k]
    return indices, probs[indices]

def classify_text(text, l1_model, l2_model, tokenizer, device, threshold=0.6):
    """
    Main classification pipeline.
    
    Args:
        text: cleaned paper text (title + abstract)
        l1_model, l2_model: loaded PyTorch models
        tokenizer: HuggingFace tokenizer
        device: torch.device
        threshold: float, if L2 confidence < threshold -> low_confidence=True
    
    Returns:
        dict with keys:
            main_category: str
            subcategory: str (or "Unclassified")
            l1_confidence: float (score of winning main category)
            l2_confidence: float (score of winning subcategory)
            low_confidence: bool
    """
    # Step 1: L1 inference
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    with torch.no_grad():
        logits = l1_model(**inputs).logits.cpu().numpy()[0]
    
    probs_l1 = softmax(logits)
    top2_indices, top2_probs = get_top_k(probs_l1, k=2)
    
    # Step 2: L2 inference for each candidate
    candidates = []  # each element: (main_idx, main_name, l1_prob, best_sub_name, l2_prob)
    for main_idx, l1_prob in zip(top2_indices, top2_probs):
        main_name = ID2MAIN[main_idx]
        # Build hint string as used during training
        hint_text = f"Main category: {main_name}\n\n{text}"
        inputs_l2 = tokenizer(hint_text, return_tensors="pt", truncation=True, max_length=512)
        inputs_l2 = {k: v.to(device) for k, v in inputs_l2.items()}
        
        with torch.no_grad():
            logits_l2 = l2_model(**inputs_l2).logits.cpu().numpy()[0]  # shape (42,)
        
        # Mask: set logits of disallowed subcategories to -inf
        allowed_ids = ALLOWED_SUB_IDS[main_idx]
        if not allowed_ids:
            raise ValueError(f"No allowed subcategories found for main category: {main_name}")
        masked_logits = np.full_like(logits_l2, -np.inf)
        for sub_id in allowed_ids:
            masked_logits[sub_id] = logits_l2[sub_id]

        # Softmax over allowed 6 (exp(-inf) = 0 so disallowed subs contribute nothing)
        probs_l2 = softmax(masked_logits)
        best_sub_id = np.argmax(probs_l2)
        best_sub_prob = probs_l2[best_sub_id]
        best_sub_name = ID2SUB[best_sub_id]
        
        candidates.append({
            "main_idx": main_idx,
            "main_name": main_name,
            "l1_prob": l1_prob,
            "sub_name": best_sub_name,
            "l2_prob": best_sub_prob,
            "combined": l1_prob * best_sub_prob
        })
    
    # Step 3: Select winner by combined score 
    winner = max(candidates, key=lambda x: x["combined"])
    main_category = winner["main_name"]
    subcategory = winner["sub_name"]
    l1_conf = winner["l1_prob"]
    l2_conf = winner["l2_prob"]
    
    # Step 4: Graceful degradation
    # Note: l2_conf is from softmax over all 42 logits (with 36 masked to -inf),
    # not a pure 6-class softmax. Scores are lower as a result. The threshold
    # of 0.6 was chosen with this in mind.
    low_confidence = bool(l2_conf < threshold)
    if low_confidence:
        subcategory = "Unclassified"
    
    return {
        "main_category": main_category,
        "subcategory": subcategory,
        "l1_confidence": float(l1_conf),
        "l2_confidence": float(l2_conf),
        "low_confidence": bool(low_confidence)
    }

# Stub replacement: the existing endpoint calls this function
# We'll keep the same function name as the original stub for seamless drop-in.
# The models and tokenizer must be loaded before this function is called.
# We'll set global variables that are initialized via main.py lifespan.

_l1_model = None
_l2_model = None
_tokenizer = None
_device = None

def initialize_models():
    # Call this once at startup (e.g., in main.py lifespan) to load models.
    global _l1_model, _l2_model, _tokenizer, _device
    _l1_model, _l2_model, _tokenizer, _device = load_models()

def classify(text: str) -> dict:
    # Public facing classification function.
    # Raises RuntimeError if models not initialized.
    if _l1_model is None:
        raise RuntimeError("Models not initialized. Call initialize_models() first.")
    return classify_text(text, _l1_model, _l2_model, _tokenizer, _device, threshold=0.6)