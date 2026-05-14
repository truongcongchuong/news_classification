import pandas as pd
import ast
import seaborn as sns
import matplotlib.pyplot as plt

from sklearn.preprocessing import MultiLabelBinarizer

# =========================
# LOAD DATA
# =========================

df = pd.read_csv("Data.csv")

df["labels"] = df["labels"].apply(ast.literal_eval)

# =========================
# MULTI HOT ENCODING
# =========================

mlb = MultiLabelBinarizer()

multi_hot = mlb.fit_transform(df["labels"])

label_names = mlb.classes_

# =========================
# COOCCURRENCE MATRIX
# =========================

co_matrix = multi_hot.T @ multi_hot

co_df = pd.DataFrame(
    co_matrix,
    index=label_names,
    columns=label_names
)

# =========================
# HEATMAP
# =========================

plt.figure(figsize=(14, 12))

sns.heatmap(
    co_df,
    annot=True,
    fmt="d",
    cmap="Blues"
)

plt.title("Label Co-occurrence Matrix")

plt.xticks(rotation=45, ha="right")

plt.tight_layout()

plt.show()