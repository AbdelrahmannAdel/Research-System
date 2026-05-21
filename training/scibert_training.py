import os
import gc
import json
import random

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding,
)
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report

# Reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
torch.cuda.manual_seed_all(SEED)

# Config
MODEL_NAME   = "allenai/scibert_scivocab_uncased"
DATASET_PATH = "/data/datasets/202011874/research-papers-dataset-combined.csv"
SAVE_L1      = "/data/datasets/202011874/scibert_l1"
SAVE_L2      = "/data/datasets/202011874/scibert_l2"

# GPU check
print("Torch version :", torch.__version__)
print("CUDA available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU           :", torch.cuda.get_device_name(0))
else:
    print("WARNING: No GPU — go to Kaggle → Settings → Accelerator → GPU T4 x1")

df = pd.read_csv(DATASET_PATH)

print(f"Dataset shape : {df.shape}")
print(f"Columns       : {df.columns.tolist()}")
print(f"Total papers  : {len(df):,}")
print()
print(df.head(3))

# Combine title + abstract into one text field used for both models
df["text"] = df["title"].astype(str) + "\n\n" + df["abstract"].astype(str)

# Sorted lists → deterministic, reproducible label order across runs
main_categories = sorted(df["main_label"].unique())
sub_categories  = sorted(df["sub_label"].unique())

print(f"\nL1 main categories ({len(main_categories)}): {main_categories}")
print(f"L2 sub  categories ({len(sub_categories )})")

# Label → integer mappings
# String keys in id2label so JSON round-trips cleanly (JSON only allows str keys)

main_label2id = {label: idx for idx, label in enumerate(main_categories)}
id2main_label = {str(idx): label for label, idx in main_label2id.items()}

sub_label2id  = {label: idx for idx, label in enumerate(sub_categories)}
id2sub_label  = {str(idx): label for label, idx in sub_label2id.items()}

df["main_label_id"] = df["main_label"].map(main_label2id)
df["sub_label_id"]  = df["sub_label"].map(sub_label2id)

# Persist mappings to disk
# These go into backend/models/scibert_l1/ and scibert_l2/ alongside the weights
os.makedirs("label_mappings", exist_ok=True)

for fname, obj in [
    ("label_mappings/main_label2id.json", main_label2id),
    ("label_mappings/main_id2label.json", id2main_label),
    ("label_mappings/sub_label2id.json",  sub_label2id),
    ("label_mappings/sub_id2label.json",  id2sub_label),
]:
    with open(fname, "w") as f:
        json.dump(obj, f, indent=2)

print("Label mappings saved to label_mappings/")
print()
print("Sample encoding:")
print(df[["main_label", "main_label_id", "sub_label", "sub_label_id"]].head(5).to_string(index=False))

# Stratify on sub_label — every subcategory belongs to exactly one main category,
# so this automatically balances both levels simultaneously.

train_df, temp_df = train_test_split(
    df,
    test_size=0.2,
    stratify=df["sub_label"],
    random_state=SEED,
)

val_df, test_df = train_test_split(
    temp_df,
    test_size=0.5,
    stratify=temp_df["sub_label"],
    random_state=SEED,
)

print(f"Full dataset : {len(df):,} papers")
print(f"Training     : {len(train_df):,} ({len(train_df)/len(df)*100:.1f}%)")
print(f"Validation   : {len(val_df):,}  ({len(val_df)/len(df)*100:.1f}%)")
print(f"Test         : {len(test_df):,}  ({len(test_df)/len(df)*100:.1f}%)")
print()
print("Training set main-category distribution:")
print(train_df["main_label"].value_counts().to_string())

# Save splits for reproducibility
train_df.to_csv("train_split.csv", index=False)
val_df.to_csv("val_split.csv",   index=False)
test_df.to_csv("test_split.csv",  index=False)
print("\nSplits saved to CSV.")

tokenizer    = AutoTokenizer.from_pretrained(MODEL_NAME)
data_collator = DataCollatorWithPadding(tokenizer=tokenizer)  # dynamic padding — faster than static max_length

# L1 tokenization: title + abstract, no hint
def tokenize_l1(batch):
    return tokenizer(
        batch["text"],
        truncation=True,
        max_length=512,
    )

# L2 tokenization: prepend main-category hint
# The hint gives the model context about which main category the paper belongs to,
# making the 42-class subcategory problem significantly easier.
def tokenize_l2(batch):
    hints = [
        f"Main category: {main}\n\n{text}"
        for main, text in zip(batch["main_label"], batch["text"])
    ]
    return tokenizer(
        hints,
        truncation=True,
        max_length=512,
    )

print("Tokenizer loaded:", MODEL_NAME)

# Convert splits to HuggingFace Datasets
train_dataset = Dataset.from_pandas(train_df.reset_index(drop=True))
val_dataset   = Dataset.from_pandas(val_df.reset_index(drop=True))

# L1 datasets (abstract, label = main_label_id)
keep_l1 = ["input_ids", "attention_mask", "main_label_id"]
drop_l1 = [c for c in train_dataset.column_names if c not in keep_l1]

tokenized_train_l1 = train_dataset.map(tokenize_l1, batched=True, remove_columns=drop_l1)
tokenized_val_l1   = val_dataset.map(tokenize_l1,   batched=True, remove_columns=drop_l1)
tokenized_train_l1 = tokenized_train_l1.rename_column("main_label_id", "labels")
tokenized_val_l1   = tokenized_val_l1.rename_column("main_label_id",   "labels")

# L2 datasets (hint + abstract, label = sub_label_id)
keep_l2 = ["input_ids", "attention_mask", "sub_label_id"]
drop_l2 = [c for c in train_dataset.column_names if c not in keep_l2]

tokenized_train_l2 = train_dataset.map(tokenize_l2, batched=True, remove_columns=drop_l2)
tokenized_val_l2   = val_dataset.map(tokenize_l2,   batched=True, remove_columns=drop_l2)
tokenized_train_l2 = tokenized_train_l2.rename_column("sub_label_id", "labels")
tokenized_val_l2   = tokenized_val_l2.rename_column("sub_label_id",   "labels")

# PyTorch tensor format
for ds in [tokenized_train_l1, tokenized_val_l1, tokenized_train_l2, tokenized_val_l2]:
    ds.set_format("torch", columns=["input_ids", "attention_mask", "labels"])

print("Tokenization complete.")
print(f"  Train L1 : {len(tokenized_train_l1):,}  |  Val L1 : {len(tokenized_val_l1):,}")
print(f"  Train L2 : {len(tokenized_train_l2):,}  |  Val L2 : {len(tokenized_val_l2):,}")

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {
        "accuracy"   : accuracy_score(labels, preds),
        "weighted_f1": f1_score(labels, preds, average="weighted"),
    }

l1_model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=len(main_categories),
    id2label=id2main_label,
    label2id=main_label2id,
    problem_type="single_label_classification",
)

training_args_l1 = TrainingArguments(
    output_dir="./results_l1",

    num_train_epochs=3,
    learning_rate=2e-5,
    weight_decay=0.01,

    per_device_train_batch_size=16,
    per_device_eval_batch_size=32,

    eval_strategy="epoch",
    save_strategy="epoch",
    save_total_limit=1,                     # only keep the best checkpoint
    load_best_model_at_end=True,
    metric_for_best_model="weighted_f1",
    greater_is_better=True,

    logging_strategy="steps",
    logging_steps=50,

    fp16=torch.cuda.is_available(),                              # mixed precision — ~2x speed on T4
    # gradient_checkpointing removed — batch_size=16 + fp16 fits T4 16GB fine
    report_to="none",
)

l1_trainer = Trainer(
    model=l1_model,
    args=training_args_l1,
    train_dataset=tokenized_train_l1,
    eval_dataset=tokenized_val_l1,
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)

l1_trainer.train(resume_from_checkpoint=True)

l1_val_results = l1_trainer.evaluate()
print("\nL1 Validation Results:")
for k, v in l1_val_results.items():
    print(f"  {k}: {v:.4f}")

# Save L1 model, tokenizer, and label mapping
os.makedirs(SAVE_L1, exist_ok=True)
l1_trainer.save_model(SAVE_L1)
tokenizer.save_pretrained(SAVE_L1)

with open(f"{SAVE_L1}/label_mapping.json", "w") as f:
    json.dump({"id2label": id2main_label, "label2id": main_label2id}, f, indent=2)

print(f"L1 model saved to {SAVE_L1}/")

# Tokenize test set for L1 BEFORE freeing trainer
# Must happen here because l1_trainer is deleted below and Block 8 needs the results.

test_dataset_tmp = Dataset.from_pandas(test_df.reset_index(drop=True))

keep_test_l1 = ["input_ids", "attention_mask", "main_label_id"]
drop_test_l1 = [c for c in test_dataset_tmp.column_names if c not in keep_test_l1]

tokenized_test_l1 = test_dataset_tmp.map(tokenize_l1, batched=True, remove_columns=drop_test_l1)
tokenized_test_l1 = tokenized_test_l1.rename_column("main_label_id", "labels")
tokenized_test_l1.set_format("torch", columns=["input_ids", "attention_mask", "labels"])

# Evaluate L1 on test set while l1_trainer still exists
l1_test_metrics = l1_trainer.evaluate(eval_dataset=tokenized_test_l1)

with open("./l1_test_metrics.json", "w") as f:
    json.dump(l1_test_metrics, f, indent=2)

print("L1 Test Results (saved to l1_test_metrics.json):")
for k, v in l1_test_metrics.items():
    print(f"  {k}: {v:.4f}")

# Free GPU memory before loading L2
# Two 110M-parameter BERT models can't both live on a T4 at once.

del tokenized_train_l1, tokenized_val_l1, tokenized_test_l1
del l1_model, l1_trainer

gc.collect()
torch.cuda.empty_cache()

print("\nL1 memory freed. Ready for L2 training.")

# Fresh load from pre-trained weights — NOT from the L1 model
l2_model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=len(sub_categories),
    id2label=id2sub_label,
    label2id=sub_label2id,
    problem_type="single_label_classification",
)

training_args_l2 = TrainingArguments(
    output_dir="./results_l2",

    num_train_epochs=2,
    learning_rate=2e-5,
    weight_decay=0.01,

    per_device_train_batch_size=16,
    per_device_eval_batch_size=32,

    eval_strategy="epoch",
    save_strategy="epoch",
    save_total_limit=1,
    load_best_model_at_end=True,
    metric_for_best_model="weighted_f1",
    greater_is_better=True,

    logging_strategy="steps",
    logging_steps=50,

    fp16=torch.cuda.is_available(),                              # mixed precision — ~2x speed on T4
    # gradient_checkpointing removed — batch_size=16 + fp16 fits T4 16GB fine
    report_to="none",
)

l2_trainer = Trainer(
    model=l2_model,
    args=training_args_l2,
    train_dataset=tokenized_train_l2,
    eval_dataset=tokenized_val_l2,
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)

# resume_from_checkpoint=False ensures L2 always trains from the base SciBERT
# weights, not L1's checkpoint. The two models solve different tasks and
# sharing a checkpoint would corrupt L2's starting point.
l2_trainer.train(resume_from_checkpoint=False)

l2_val_results = l2_trainer.evaluate()
print("\nL2 Validation Results:")
for k, v in l2_val_results.items():
    print(f"  {k}: {v:.4f}")

# Save L2 model, tokenizer, and label mapping
os.makedirs(SAVE_L2, exist_ok=True)
l2_trainer.save_model(SAVE_L2)
tokenizer.save_pretrained(SAVE_L2)

with open(f"{SAVE_L2}/label_mapping.json", "w") as f:
    json.dump({"id2label": id2sub_label, "label2id": sub_label2id}, f, indent=2)

# Save test set now so it's safe even if the notebook crashes later
test_df.to_csv("test_set.csv", index=False)

print(f"L2 model saved to {SAVE_L2}/")
print(f"Test set saved  : test_set.csv ({len(test_df):,} papers)")

print("Running L2 inference on validation set for threshold tuning...")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
l2_model.eval()
l2_model.to(device)

all_confidences = []
all_correct     = []

val_loader = DataLoader(tokenized_val_l2, batch_size=64)

with torch.no_grad():
    for batch in val_loader:
        input_ids      = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        true_labels    = batch["labels"]

        logits = l2_model(input_ids=input_ids, attention_mask=attention_mask).logits
        probs  = F.softmax(logits, dim=-1)

        confidences, predicted_ids = probs.max(dim=-1)

        confidences   = confidences.cpu().numpy()
        predicted_ids = predicted_ids.cpu().numpy()
        true_labels   = true_labels.numpy()

        for conf, pred, true in zip(confidences, predicted_ids, true_labels):
            all_confidences.append(float(conf))
            all_correct.append(int(pred == true))

all_confidences = np.array(all_confidences)
all_correct     = np.array(all_correct)

print(f"Inference complete on {len(all_confidences):,} validation papers\n")

# Scan thresholds
print(f"{'Threshold':>10} {'Accuracy':>10} {'% Classified':>14} {'Papers':>10}")
print("-" * 50)

best_threshold = 0.6
best_accuracy  = 0.0

for threshold in np.arange(0.0, 1.01, 0.05):
    above_mask = all_confidences >= threshold
    n_shown    = above_mask.sum()

    if n_shown == 0:
        continue

    acc_shown        = all_correct[above_mask].mean()
    pct_classified   = above_mask.mean() * 100
    pct_unclassified = 100 - pct_classified

    print(f"{threshold:>10.2f} {acc_shown:>10.4f} {pct_classified:>13.1f}% {n_shown:>10,}")

    # Best threshold = highest accuracy while classifying at least 80% of papers
    if acc_shown > best_accuracy and pct_unclassified < 20:
        best_accuracy  = acc_shown
        best_threshold = threshold

print(f"\n{'='*50}")
print(f"Recommended threshold : {best_threshold:.2f}")
print(f"Accuracy at threshold : {best_accuracy:.4f}")
print(f"\n→ Set LOW_CONFIDENCE_THRESHOLD = {best_threshold:.2f} in classifier.py")

print("Running final evaluation on the held-out test set...\n")

test_dataset = Dataset.from_pandas(test_df.reset_index(drop=True))

# L1 test results
with open("./l1_test_metrics.json") as f:
    l1_test = json.load(f)

print("L1 Test Results — Main Category (7 classes):")
for k, v in l1_test.items():
    print(f"  {k}: {v:.4f}")

print()

# Tokenize test set for L2
keep_test_l2 = ["input_ids", "attention_mask", "sub_label_id"]
drop_test_l2 = [c for c in test_dataset.column_names if c not in keep_test_l2]

tokenized_test_l2 = test_dataset.map(tokenize_l2, batched=True, remove_columns=drop_test_l2)
tokenized_test_l2 = tokenized_test_l2.rename_column("sub_label_id", "labels")
tokenized_test_l2.set_format("torch", columns=["input_ids", "attention_mask", "labels"])

# L2 test results (l2_trainer is still alive)
l2_test = l2_trainer.evaluate(eval_dataset=tokenized_test_l2)
print("L2 Test Results — Subcategory (42 classes):")
for k, v in l2_test.items():
    print(f"  {k}: {v:.4f}")

print()
print("These are your final honest numbers — use them in the capstone report/presentation.")

# Detailed per-class classification report for L2 (useful for the presentation)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
l2_model.eval()
l2_model.to(device)

all_preds  = []
all_labels = []

test_loader = DataLoader(tokenized_test_l2, batch_size=64)

with torch.no_grad():
    for batch in test_loader:
        input_ids      = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        true_labels    = batch["labels"]

        logits = l2_model(input_ids=input_ids, attention_mask=attention_mask).logits
        preds  = logits.argmax(dim=-1).cpu().numpy()

        all_preds.extend(preds)
        all_labels.extend(true_labels.numpy())

target_names = [id2sub_label[str(i)] for i in range(len(sub_categories))]

print("L2 Per-Class Classification Report:")
print(classification_report(all_labels, all_preds, target_names=target_names, digits=3))
