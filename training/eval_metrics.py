"""
eval_metrics.py
---------------
Run after training is complete. Loads scibert_l1 and scibert_l2 from disk,
tokenizes the held-out test set, and prints full per-class classification
reports for both models.

Run from the work directory:
    cd /data/datasets/202011874
    python eval_metrics.py
"""

import json
import numpy as np
import pandas as pd
import torch
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, DataCollatorWithPadding, Trainer, TrainingArguments
from sklearn.metrics import classification_report, accuracy_score, f1_score

# ── Paths ─────────────────────────────────────────────────────────────────────
WORK_DIR       = "/data/datasets/202011874"
TEST_CSV       = f"{WORK_DIR}/test_set.csv"
MODEL_L1       = f"{WORK_DIR}/scibert_l1"
MODEL_L2       = f"{WORK_DIR}/scibert_l2"
LABEL_MAPPINGS = f"{WORK_DIR}/label_mappings"

# ── Load label mappings ───────────────────────────────────────────────────────
with open(f"{LABEL_MAPPINGS}/main_id2label.json") as f:
    id2main_label = json.load(f)

with open(f"{LABEL_MAPPINGS}/sub_id2label.json") as f:
    id2sub_label = json.load(f)

with open(f"{LABEL_MAPPINGS}/main_label2id.json") as f:
    main_label2id = json.load(f)

with open(f"{LABEL_MAPPINGS}/sub_label2id.json") as f:
    sub_label2id = json.load(f)

# ── Load test set ─────────────────────────────────────────────────────────────
print("Loading test set...")
test_df = pd.read_csv(TEST_CSV)
print(f"Test set: {len(test_df):,} papers")

test_df["text"] = test_df["title"].astype(str) + "\n\n" + test_df["abstract"].astype(str)
test_df["main_label_id"] = test_df["main_label"].map(main_label2id)
test_df["sub_label_id"]  = test_df["sub_label"].map(sub_label2id)

# ── Tokenizer ─────────────────────────────────────────────────────────────────
print("Loading tokenizer...")
tokenizer     = AutoTokenizer.from_pretrained(MODEL_L1)
data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

# ── Tokenization functions ────────────────────────────────────────────────────
def tokenize_l1(batch):
    return tokenizer(batch["text"], truncation=True, max_length=512)

def tokenize_l2(batch):
    hints = [
        f"Main category: {main}\n\n{text}"
        for main, text in zip(batch["main_label"], batch["text"])
    ]
    return tokenizer(hints, truncation=True, max_length=512)

# ── Metrics helper ────────────────────────────────────────────────────────────
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {
        "accuracy"   : accuracy_score(labels, preds),
        "weighted_f1": f1_score(labels, preds, average="weighted"),
    }

# ═══════════════════════════════════════════════════════════════════════════════
# L1 EVALUATION
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("L1 EVALUATION — Main Category (7 classes)")
print("="*60)

print("Tokenizing L1 test set...")
test_ds = Dataset.from_pandas(test_df.reset_index(drop=True))
keep_l1 = ["input_ids", "attention_mask", "main_label_id"]
drop_l1 = [c for c in test_ds.column_names if c not in keep_l1]
tokenized_test_l1 = test_ds.map(tokenize_l1, batched=True, remove_columns=drop_l1)
tokenized_test_l1 = tokenized_test_l1.rename_column("main_label_id", "labels")
tokenized_test_l1.set_format("torch", columns=["input_ids", "attention_mask", "labels"])

print("Loading L1 model...")
l1_model = AutoModelForSequenceClassification.from_pretrained(MODEL_L1)

# Use a minimal TrainingArguments just to run evaluate()
l1_args = TrainingArguments(
    output_dir="./eval_tmp",
    per_device_eval_batch_size=32,
    fp16=torch.cuda.is_available(),
    report_to="none",
)

l1_trainer = Trainer(
    model=l1_model,
    args=l1_args,
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)

l1_results = l1_trainer.evaluate(eval_dataset=tokenized_test_l1)
print(f"\nL1 Overall:")
print(f"  Accuracy    : {l1_results['eval_accuracy']:.4f}")
print(f"  Weighted F1 : {l1_results['eval_weighted_f1']:.4f}")
print(f"  Loss        : {l1_results['eval_loss']:.4f}")

# Per-class report
print("\nL1 Per-Class Report:")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
l1_model.eval()
l1_model.to(device)

from torch.utils.data import DataLoader
all_preds, all_labels = [], []
for batch in DataLoader(tokenized_test_l1, batch_size=64, collate_fn=data_collator):
    with torch.no_grad():
        logits = l1_model(
            input_ids=batch["input_ids"].to(device),
            attention_mask=batch["attention_mask"].to(device)
        ).logits
    all_preds.extend(logits.argmax(dim=-1).cpu().numpy())
    all_labels.extend(batch["labels"].numpy())

l1_target_names = [id2main_label[str(i)] for i in range(len(id2main_label))]
print(classification_report(all_labels, all_preds, target_names=l1_target_names, digits=3))

# Save to disk
l1_report = classification_report(all_labels, all_preds, target_names=l1_target_names, digits=3, output_dict=True)
with open(f"{WORK_DIR}/l1_full_report.json", "w") as f:
    json.dump(l1_report, f, indent=2)
print("Saved → l1_full_report.json")

# Free L1 from GPU
del l1_model, l1_trainer, tokenized_test_l1
import gc; gc.collect(); torch.cuda.empty_cache()

# ═══════════════════════════════════════════════════════════════════════════════
# L2 EVALUATION
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("L2 EVALUATION — Subcategory (42 classes)")
print("="*60)

print("Tokenizing L2 test set...")
test_ds2 = Dataset.from_pandas(test_df.reset_index(drop=True))
keep_l2  = ["input_ids", "attention_mask", "sub_label_id"]
drop_l2  = [c for c in test_ds2.column_names if c not in keep_l2]
tokenized_test_l2 = test_ds2.map(tokenize_l2, batched=True, remove_columns=drop_l2)
tokenized_test_l2 = tokenized_test_l2.rename_column("sub_label_id", "labels")
tokenized_test_l2.set_format("torch", columns=["input_ids", "attention_mask", "labels"])

print("Loading L2 model...")
l2_model = AutoModelForSequenceClassification.from_pretrained(MODEL_L2)

l2_args = TrainingArguments(
    output_dir="./eval_tmp",
    per_device_eval_batch_size=32,
    fp16=torch.cuda.is_available(),
    report_to="none",
)

l2_trainer = Trainer(
    model=l2_model,
    args=l2_args,
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)

l2_results = l2_trainer.evaluate(eval_dataset=tokenized_test_l2)
print(f"\nL2 Overall:")
print(f"  Accuracy    : {l2_results['eval_accuracy']:.4f}")
print(f"  Weighted F1 : {l2_results['eval_weighted_f1']:.4f}")
print(f"  Loss        : {l2_results['eval_loss']:.4f}")

# Per-class report
print("\nL2 Per-Class Report:")
l2_model.eval()
l2_model.to(device)

all_preds, all_labels = [], []
for batch in DataLoader(tokenized_test_l2, batch_size=64, collate_fn=data_collator):
    with torch.no_grad():
        logits = l2_model(
            input_ids=batch["input_ids"].to(device),
            attention_mask=batch["attention_mask"].to(device)
        ).logits
    all_preds.extend(logits.argmax(dim=-1).cpu().numpy())
    all_labels.extend(batch["labels"].numpy())

l2_target_names = [id2sub_label[str(i)] for i in range(len(id2sub_label))]
print(classification_report(all_labels, all_preds, target_names=l2_target_names, digits=3))

# Save to disk
l2_report = classification_report(all_labels, all_preds, target_names=l2_target_names, digits=3, output_dict=True)
with open(f"{WORK_DIR}/l2_full_report.json", "w") as f:
    json.dump(l2_report, f, indent=2)
print("Saved → l2_full_report.json")

print("\n" + "="*60)
print("Done. Reports saved to:")
print(f"  {WORK_DIR}/l1_full_report.json")
print(f"  {WORK_DIR}/l2_full_report.json")
print("="*60)
