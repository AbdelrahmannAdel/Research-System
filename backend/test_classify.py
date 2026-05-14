import sys, torch, json, unicodedata, re
import numpy as np
sys.path.insert(0, '.')
from app.services.pdf_extractor import extract_from_pdf
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# Extract exact text the system would use
with open('C:/users/hp/Desktop/papers to test/CCCCCC.pdf', 'rb') as f:
    file_bytes = f.read()

extracted = extract_from_pdf(file_bytes)

abstract = extracted['abstract'] or extracted['intro'] or extracted['summary_input']
abstract = unicodedata.normalize('NFKC', abstract)
abstract = re.sub(r'-\n', '', abstract)
abstract = re.sub(r'\n', ' ', abstract)
title = unicodedata.normalize('NFKC', extracted['title'] or '')
classify_input = title + '\n\n' + abstract

print('=== CLASSIFY INPUT ===')
print(classify_input[:500])
print('...')
print(f'Total chars: {len(classify_input)}')

# Load model and classify
tokenizer = AutoTokenizer.from_pretrained('models/scibert_l1', local_files_only=True)
l1_model = AutoModelForSequenceClassification.from_pretrained('models/scibert_l1', local_files_only=True)
l1_model.eval()

with open('models/label_mappings/main_id2label.json') as f:
    id2main = {int(k): v for k, v in json.load(f).items()}

with torch.no_grad():
    inputs = tokenizer(classify_input, return_tensors='pt', truncation=True, max_length=512)
    print(f'Token count: {inputs["input_ids"].shape[1]}')
    logits = l1_model(**inputs).logits.cpu().numpy()[0]
    probs = np.exp(logits) / np.sum(np.exp(logits))

print()
print('=== RESULTS ===')
for i, (l, p) in enumerate(zip(logits, probs)):
    print(f'{id2main[i]}: logit={l:.4f}, prob={p:.4f}')
winner = int(np.argmax(logits))
print(f'\nWinner: {id2main[winner]}')
