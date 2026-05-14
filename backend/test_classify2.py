import sys, torch, json, unicodedata, re
import numpy as np
sys.path.insert(0, '.')
from transformers import AutoModelForSequenceClassification, AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained('models/scibert_l1', local_files_only=True)
model = AutoModelForSequenceClassification.from_pretrained('models/scibert_l1', local_files_only=True)
model.eval()

with open('models/label_mappings/main_id2label.json') as f:
    id2main = {int(k): v for k, v in json.load(f).items()}

title = 'Compute Where it Counts: Self Optimizing Language Models'
abstract = 'Efficient LLM inference research has largely focused on reducing the cost of each decoding step (e.g., using quantization, pruning, or sparse attention), typically applying a uniform computation budget to every generated token. In practice, token difficulty varies widely, so static compression can over-compute on easy steps and undercompute on hard ones. We study dynamic budget allocation for autoregressive decoding: learning how much computation to spend per token from within a single model. Self-Optimizing Language Models (SOL) pair a frozen LLM with a lightweight policy network that reads the LLM hidden state and selects a discrete efficiency action at each decode step. Actions can jointly control (i) token-level attention sparsity, (ii) structured activation pruning in the MLP, and (iii) activation quantization bit-width, while leaving the base model weights unchanged. We train the policy with group-relative policy optimization on teacher-forced episodes: the token sequence is fixed, while we sample multiple compute schedules (i.e., \u201ccounterfactual\u201d schedules that vary only the efficiency actions for the same token path) and compare their likelihoods under the same supervision. Our reward trades off language-model quality against soft penalties that encourage episode-average budget usage to match a requested target. Across model variants and compute regimes, SOL improves quality at matched budget over static allocation and strong random schedule search, offering a complementary axis for inference-efficiency optimization. SOL discovers a better quality-efficiency paretofront across all our experiments and improves MMLU accuracy by up to 7.3% over uniform budget allocation strategies.'

# Test 1: title + \n\n + abstract (what the system sends)
text_system = title + '\n\n' + abstract
# Test 2: title + space + abstract (what your working test used)
text_space = title + ' ' + abstract
# Test 3: abstract only
text_abstract_only = abstract

for label, text in [
    ('title + \\n\\n + abstract', text_system),
    ('title + space + abstract', text_space),
    ('abstract only', text_abstract_only),
]:
    with torch.no_grad():
        inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
        logits = model(**inputs).logits.cpu().numpy()[0]
        probs = np.exp(logits) / np.sum(np.exp(logits))
    winner = int(np.argmax(logits))
    print(f'\n--- {label} ---')
    print(f'Tokens: {inputs["input_ids"].shape[1]}')
    for i, (l, p) in enumerate(zip(logits, probs)):
        print(f'  {id2main[i]}: logit={l:.4f}, prob={p:.4f}')
    print(f'Winner: {id2main[winner]}')
