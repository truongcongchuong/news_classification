import pandas as pd
import ast
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel
import torch.nn as nn
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from tqdm import tqdm

# =========================
# 1. ĐỌC DỮ LIỆU
# =========================
df = pd.read_csv("cleaned_data.csv")

df['labels'] = df['labels'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
# =========================
# 3. MULTI LABEL ENCODING
# =========================

mlb = MultiLabelBinarizer()

y = mlb.fit_transform(df["labels"])

print("Classes:")
print(mlb.classes_)

# =========================
# 4. TRAIN TEST SPLIT
# =========================

train_texts, val_texts, train_labels, val_labels = train_test_split(
    df["text"].tolist(),
    y,
    test_size=0.2,
    random_state=42
)

# =========================
# 5. TOKENIZER
# =========================

MODEL_NAME = "vinai/phobert-base"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

MAX_LEN = 256

# =========================
# 6. DATASET
# =========================

class NewsDataset(Dataset):

    def __init__(self, texts, labels):
        self.texts = texts
        self.labels = labels

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):

        text = str(self.texts[idx])

        encoding = tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=MAX_LEN,
            return_tensors="pt"
        )

        item = {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "labels": torch.tensor(
                self.labels[idx],
                dtype=torch.float
            )
        }

        return item

train_dataset = NewsDataset(train_texts, train_labels)
val_dataset = NewsDataset(val_texts, val_labels)

train_loader = DataLoader(
    train_dataset,
    batch_size=8,
    shuffle=True
)

val_loader = DataLoader(
    val_dataset,
    batch_size=8
)

# =========================
# 7. MODEL
# =========================

class PhoBERTClassifier(nn.Module):

    def __init__(self, num_classes):

        super().__init__()

        self.phobert = AutoModel.from_pretrained(MODEL_NAME)

        self.dropout = nn.Dropout(0.3)

        self.fc = nn.Linear(768, num_classes)

    def forward(self, input_ids, attention_mask):

        outputs = self.phobert(
            input_ids=input_ids,
            attention_mask=attention_mask
        )

        # Lấy vector CLS
        cls_output = outputs.last_hidden_state[:, 0, :]

        x = self.dropout(cls_output)

        logits = self.fc(x)

        return logits

# =========================
# 8. DEVICE
# =========================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("Using device:", device)

model = PhoBERTClassifier(
    num_classes=len(mlb.classes_)
)

model.to(device)

# =========================
# 9. LOSS + OPTIMIZER
# =========================

criterion = nn.BCEWithLogitsLoss()

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=2e-5
)

# =========================
# 10. TRAINING LOOP
# =========================

EPOCHS = 3

for epoch in range(EPOCHS):

    model.train()

    total_loss = 0

    loop = tqdm(train_loader)

    for batch in loop:

        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)

        optimizer.zero_grad()

        logits = model(
            input_ids,
            attention_mask
        )

        loss = criterion(logits, labels)

        loss.backward()

        optimizer.step()

        total_loss += loss.item()

        loop.set_description(
            f"Epoch {epoch+1}"
        )

        loop.set_postfix(
            loss=loss.item()
        )

    avg_loss = total_loss / len(train_loader)

    print(f"\nEpoch {epoch+1} Loss: {avg_loss:.4f}")

# =========================
# 11. EVALUATION
# =========================

model.eval()

all_preds = []
all_labels = []

with torch.no_grad():

    for batch in tqdm(val_loader):

        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)

        labels = batch["labels"].cpu().numpy()

        logits = model(
            input_ids,
            attention_mask
        )

        probs = torch.sigmoid(logits)

        preds = (probs > 0.5).int().cpu().numpy()

        all_preds.extend(preds)
        all_labels.extend(labels)

# =========================
# 12. REPORT
# =========================

print(
    classification_report(
        all_labels,
        all_preds,
        target_names=mlb.classes_,
        zero_division=0
    )
)