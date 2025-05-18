import pandas as pd

# Mapping of file names to the columns you want to extract
file_column_map = {
    r"B:\tut-pricing-model\shampoos\shampoo-alnahdi.json":  {"name_col": 'Product Name', "price_col": 'Price'},
    r"B:\tut-pricing-model\shampoos\shampoo-amazon.json": {"name_col": "title", "price_col": "price"},
    r"B:\tut-pricing-model\shampoos\shampoo-dawaa.json": {"name_col": "name", "price_col": "price"},
    r"B:\tut-pricing-model\shampoos\shampoo-noon.json": {"name_col": "Product Name", "price_col": "Price"}
}
for file in file_column_map:
    try:
        df = pd.read_json(file)
        print(f"\n{file} columns:")
        print(df.columns.tolist())
    except Exception as e:
        print(f"❌ Error reading {file}: {e}")
# Read, rename, and combine
dfs = []
for file, cols in file_column_map.items():
    df = pd.read_json(file)
    df = df[[cols["name_col"], cols["price_col"]]]
    df.columns = ["name", "price"]  # Standardize column names
    dfs.append(df)

# Concatenate all into one DataFrame
combined_df = pd.concat(dfs, ignore_index=True)

# Optional: Clean price format
combined_df["price_numeric"] = combined_df["price"].str.replace(r"[^\d.,]", "", regex=True)

# Display preview and save
print(combined_df.head())
combined_df.to_csv("combined_shampoo.csv", index=False)
