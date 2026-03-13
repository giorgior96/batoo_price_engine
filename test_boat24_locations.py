import json
from collections import Counter
import re

with open("boat24_boats.json", "r") as f:
    data = json.load(f)

locations = [item.get("location", "") for item in data if item.get("location")]
counts = Counter(locations)

print("Esempi di località con codice tra parentesi:")
with_code = [loc for loc in counts.keys() if re.search(r'\([A-Z]{1,3}\)', loc)]
for loc in with_code[:10]:
    print(f"- {loc}")

print("\nEsempi di località SENZA codice tra parentesi:")
without_code = [loc for loc in counts.keys() if not re.search(r'\([A-Z]{1,3}\)', loc)]
# Ordiniamo per frequenza per vedere le più comuni
without_code_sorted = sorted(without_code, key=lambda x: counts[x], reverse=True)
for loc in without_code_sorted[:20]:
    print(f"- {loc} (Trovata {counts[loc]} volte)")
