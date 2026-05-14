import pandas as pd
import ast
import torch
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
from tqdm import tqdm

# =========================
# 1. LOAD DATA
# =========================

df = pd.read_csv("Data.csv")

# Xóa url
df = df.drop(columns=["url"])

# Convert labels string -> list
df["labels"] = df["labels"].apply(ast.literal_eval)

# Ghép title + content
df["text"] = (
    df["title"].astype(str)
    + " "
    + df["content"].astype(str)
)

# =========================
# 2. LOAD PHOBERT
# =========================

MODEL_NAME = "vinai/phobert-base"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

model.to(device)
model.eval()

MAX_LEN = 256

# =========================
# 3. LẤY EMBEDDING
# =========================

label_embeddings = defaultdict(list)

with torch.no_grad():

    for _, row in tqdm(df.iterrows(), total=len(df)):

        text = row["text"]

        labels = row["labels"]

        encoding = tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=MAX_LEN,
            return_tensors="pt"
        )

        input_ids = encoding["input_ids"].to(device)
        attention_mask = encoding["attention_mask"].to(device)

        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask
        )

        # CLS embedding
        embedding = (
            outputs.last_hidden_state[:, 0, :]
            .squeeze(0)
            .cpu()
            .numpy()
        )

        # Gán embedding cho từng label
        for label in labels:
            label_embeddings[label].append(embedding)

# =========================
# 4. MEAN EMBEDDING CHO MỖI LABEL
# =========================

mean_embeddings = {}

for label, vectors in label_embeddings.items():

    mean_vector = np.mean(vectors, axis=0)

    mean_embeddings[label] = mean_vector

# =========================
# 5. TẠO MA TRẬN COSINE SIMILARITY
# =========================

labels = list(mean_embeddings.keys())

embedding_matrix = np.array([
    mean_embeddings[label]
    for label in labels
])

similarity_matrix = cosine_similarity(
    embedding_matrix
)

# =========================
# 6. HEATMAP
# =========================

plt.figure(figsize=(12, 10))

sns.heatmap(
    similarity_matrix,
    xticklabels=labels,
    yticklabels=labels,
    annot=True,
    cmap="Blues",
    fmt=".2f"
)

plt.title("Label Semantic Similarity")

plt.xticks(rotation=45, ha="right")

plt.tight_layout()

plt.show()