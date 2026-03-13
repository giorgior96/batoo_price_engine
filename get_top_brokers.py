import json
from collections import Counter

# Load DB
try:
    with open('master_boats_db.json', 'r') as f:
        db = json.load(f)
except Exception as e:
    print(f"Error reading DB: {e}")
    db = []

# Filter for topboats and count by broker
topboats_brokers = [b for b in db if b.get('source') == 'topboats' and b.get('broker')]
broker_counts = Counter([b['broker'] for b in topboats_brokers])

# Print top 10 brokers and a sample URL for each
print("Top 10 brokers on Topboats:")
for broker, count in broker_counts.most_common(10):
    sample_url = next(b['url'] for b in topboats_brokers if b['broker'] == broker)
    print(f"{broker}: {count} boats (Sample URL: {sample_url})")
