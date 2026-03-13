import pandas as pd
data = [
    {"builder": "Beneteau", "model": "Oceanis 41", "price_eur": 100000},
    {"builder": "Beneteau Oceanis", "model": "50", "price_eur": 200000},
    {"builder": "Beneteau", "model": "Oceanis 41.1", "price_eur": 150000}
]
df = pd.DataFrame(data)
df['builder_search'] = df['builder'].str.lower()
df['model_search'] = df['model'].str.lower()
df['full_name'] = df['builder'].astype(str) + " " + df['model'].astype(str)
df['full_name_lower'] = df['full_name'].str.lower()

q = "Beneteau Oceanis 41"
words = q.lower().split()

# Current logic
all_builders = df['builder_search'].dropna().unique()
found_builder = None
if len(words) >= 2:
    two_words = f"{words[0]} {words[1]}"
    if two_words in all_builders:
        found_builder = two_words
        remaining_model_words = words[2:]
if not found_builder:
    if words[0] in all_builders:
        found_builder = words[0]
        remaining_model_words = words[1:]
    else:
        remaining_model_words = words

mask = pd.Series([True] * len(df))
if found_builder:
    mask = mask & (df['builder_search'] == found_builder)
for kw in remaining_model_words:
    mask = mask & (df['builder_search'].str.contains(kw, na=False, regex=False) | df['model_search'].str.contains(kw, na=False, regex=False))

print("Current logic matches:")
print(df[mask])

# New logic
mask2 = pd.Series([True] * len(df))
for kw in words:
    mask2 = mask2 & df['full_name_lower'].str.contains(kw, na=False, regex=False)

print("\nNew logic matches:")
print(df[mask2])
