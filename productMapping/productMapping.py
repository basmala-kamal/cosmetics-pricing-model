import pandas as pd
from sentence_transformers import SentenceTransformer, util
import torch

#CONFIG
csv_a_path = "B:/tut-pricing-model/tints/tint_amazon_cleaned.csv"
csv_b_path = "B:/tut-pricing-model/tints/tint_noon_cleaned.csv"
column_name_a = "title"  
column_name_b = "name"  
similarity_threshold = 0.75     

# === 1. Load CSVs ===
df_a = pd.read_csv(csv_a_path)
df_b = pd.read_csv(csv_b_path)

# Ensure column exists
if column_name_a not in df_a.columns or column_name_b not in df_b.columns:
    raise ValueError("Check column names. Make sure both CSVs contain the specified columns.")

texts_a = df_a[column_name_a].astype(str).tolist()
texts_b = df_b[column_name_b].astype(str).tolist()

# === 2. Load Sentence Transformer model ===
model = SentenceTransformer("all-MiniLM-L6-v2")  # Fast and accurate for general use

# === 3. Encode both sets of texts ===
print("Encoding text from both CSVs...")
embeddings_a = model.encode(texts_a, convert_to_tensor=True)
embeddings_b = model.encode(texts_b, convert_to_tensor=True)

# === 4. Compute cosine similarity matrix ===
print("Calculating similarities...")
cosine_scores = util.cos_sim(embeddings_a, embeddings_b)  # shape: (len_a, len_b)

# === 5. Get best match for each item in CSV A ===
print("Matching best pairs...")
matches = []

for idx_a, row in enumerate(cosine_scores):
    best_score, idx_b = torch.max(row, dim=0)
    score_value = float(best_score)

    if score_value >= similarity_threshold:
        matches.append({
            "CSV A Product": texts_a[idx_a],
            "CSV B Product": texts_b[idx_b],
            "Similarity Score": round(score_value, 4)
        })

# === 6. Save or display results ===
results_df = pd.DataFrame(matches)
results_df = results_df.sort_values("Similarity Score", ascending=False)

# Optional: Save to file
results_df.to_csv("matched_products.csv", index=False, encoding="utf-8-sig")

# Print top matches
print("\nTop Matches:")
print(results_df.head(10))
