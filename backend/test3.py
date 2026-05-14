import torch, json, numpy as np
from transformers import AutoModelForSequenceClassification, AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained('models/scibert_l1', local_files_only=True)
model = AutoModelForSequenceClassification.from_pretrained('models/scibert_l1', local_files_only=True)
model.eval()

with open('models/label_mappings/main_id2label.json') as f:
    id2main = {int(k): v for k, v in json.load(f).items()}

tests = {
    "first sentence only": "Compute Where it Counts: Self Optimizing Language Models Efficient LLM inference research has largely focused on reducing the cost of each decoding step.",
    "engineering-sounding sentences": "Compute Where it Counts: Self Optimizing Language Models We study dynamic budget allocation for autoregressive decoding. Actions can jointly control token-level attention sparsity, structured activation pruning in the MLP, and activation quantization bit-width.",
    "neutral CS sentences": "Compute Where it Counts: Self Optimizing Language Models We pair a frozen LLM with a lightweight policy network. We train the policy with group-relative policy optimization on teacher-forced episodes.",
}

for label, text in tests.items():
    with torch.no_grad():
        inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
        logits = model(**inputs).logits.cpu().numpy()[0]
        probs = np.exp(logits) / np.sum(np.exp(logits))
    winner = int(np.argmax(logits))
    print(f'\n--- {label} ---')
    for i, (l, p) in enumerate(zip(logits, probs)):
        print(f'  {id2main[i]}: logit={l:.4f}, prob={p:.4f}')
    print(f'Winner: {id2main[winner]}')
