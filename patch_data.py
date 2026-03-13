import json
import pandas as pd

with open('master_boats_db.json', 'r') as f:
    data = json.load(f)

df = pd.DataFrame(data)

# Fix comuni
df.loc[df['builder'] == 'B N Teau', 'builder'] = 'Beneteau'
df = df[df['builder'] != 'Barcheamotore']
df = df[df['builder'] != 'Barcheavela']

df.to_json('master_boats_db.json', orient='records', indent=2)
print(f"Patched DB: {len(df)} records left.")
