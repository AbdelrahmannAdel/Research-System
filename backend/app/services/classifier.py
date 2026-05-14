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
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    print(f"[CLASSIFIER] L1 path: {L1_MODEL_PATH.resolve()}")
    print(f"[CLASSIFIER] L2 path: {L2_MODEL_PATH.resolve()}")
    print(f"[CLASSIFIER] L1 path exists: {L1_MODEL_PATH.exists()}")

    tokenizer = AutoTokenizer.from_pretrained(str(L1_MODEL_PATH), local_files_only=True)
    
    l1_model = AutoModelForSequenceClassification.from_pretrained(str(L1_MODEL_PATH), local_files_only=True)
    l1_model.to(device)
    l1_model.eval()
    
    l2_model = AutoModelForSequenceClassification.from_pretrained(str(L2_MODEL_PATH), local_files_only=True)
    l2_model.to(device)
    l2_model.eval()
    
    print(f"[CLASSIFIER] L1 classifier: {l1_model.classifier}")
    print(f"[CLASSIFIER] L1 classifier bias: {l1_model.classifier.bias.data}")
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
    
    # Re-run self test inside inference
    test_inputs = _tokenizer("machine learning neural network deep learning", return_tensors="pt")
    test_inputs_device = {k: v.to(_device) for k, v in test_inputs.items()}
    with torch.no_grad():
        test_logits = _l1_model(**test_inputs_device).logits.cpu().numpy()[0]
    print(f"[CLASSIFIER] Mid-inference self-test winner: {ID2MAIN[int(np.argmax(test_logits))]}")
    print(f"[CLASSIFIER] Mid-inference self-test logits: {test_logits}")

    print(f"[CLASSIFIER] Token count: {len(tokenizer.encode(text))}")
    
    print(f"[CLASSIFIER] Token count: {len(tokenizer.encode(text))}")
    print(f"[CLASSIFIER] grad enabled: {torch.is_grad_enabled()}")
    print(f"[CLASSIFIER] training mode: {_l1_model.training}")
    print(f"[CLASSIFIER] model id in classify_text: {id(_l1_model)}")
    print(f"[CLASSIFIER] Full text:\n{text}\n---")
    
    # Step 1: L1 inference
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    print(f"[CLASSIFIER] input_ids first 20: {inputs['input_ids'][0][:20]}")
    print(f"[CLASSIFIER] input_ids last 20: {inputs['input_ids'][0][-20:]}")
    print(f"[CLASSIFIER] total tokens: {inputs['input_ids'].shape[1]}")
    print(f"[CLASSIFIER] decoded: {tokenizer.decode(inputs['input_ids'][0][:20])}")
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    print(f"[CLASSIFIER] input_ids going into model: {inputs['input_ids'][0][:20]}")
    print(f"[CLASSIFIER] attention_mask: {inputs['attention_mask'][0][:20]}")
    print(f"[CLASSIFIER] inputs keys: {list(inputs.keys())}")
    if 'token_type_ids' in inputs:
        print(f"[CLASSIFIER] token_type_ids: {inputs['token_type_ids'][0][:20]}")
    with torch.no_grad():
        logits = l1_model(**inputs).logits.cpu().numpy()[0]
        
    print(f"[CLASSIFIER] L1 raw logits: {logits}")
    print(f"[CLASSIFIER] L1 probs: {softmax(logits)}")
    
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
        
        # Extract only the 6 allowed subcategory logits
        allowed_ids = ALLOWED_SUB_IDS[main_idx]
        if not allowed_ids:
            raise ValueError(f"No allowed subcategories found for main category: {main_name}")

        allowed_ids_list = sorted(allowed_ids)                                    # list of 6 ints, deterministic order
        allowed_logits = np.array([logits_l2[i] for i in allowed_ids_list])      # shape (6,)

        # Softmax over these 6 only
        exp = np.exp(allowed_logits - np.max(allowed_logits))
        probs_6 = exp / np.sum(exp)

        best_local_idx = int(np.argmax(probs_6))         # 0..5
        best_sub_id = allowed_ids_list[best_local_idx]   # actual global id 0..41
        best_sub_prob = float(probs_6[best_local_idx])
        best_sub_name = ID2SUB[best_sub_id]
        
        print(f"[CLASSIFIER] {main_name} → {best_sub_name} (l2={best_sub_prob:.3f})")
        
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
    global _l1_model, _l2_model, _tokenizer, _device
    print(f"[CLASSIFIER] initialize_models called")
    _l1_model, _l2_model, _tokenizer, _device = load_models()
    print(f"[CLASSIFIER] models set, l1 id: {id(_l1_model)}")
    
    # Self-test: run inference immediately after loading
    test_inputs = _tokenizer("machine learning neural network deep learning", return_tensors="pt")
    test_inputs = {k: v.to(_device) for k, v in test_inputs.items()}
    with torch.no_grad():
        test_logits = _l1_model(**test_inputs).logits.cpu().numpy()[0]
    print(f"[CLASSIFIER] Self-test logits: {test_logits}")
    print(f"[CLASSIFIER] Self-test winner: {ID2MAIN[int(np.argmax(test_logits))]}")

def classify(text: str) -> dict:
    if _l1_model is None:
        raise RuntimeError("Models not initialized. Call initialize_models() first.")
    with torch.no_grad():
        return classify_text(text, _l1_model, _l2_model, _tokenizer, _device, threshold=0.6)