import pandas as pd
import json

with open("results.json") as f:
    data = json.load(f)

rows = []
for entry in data:
    flags = entry["flags"].split()
    results = entry["results"]

    total_time = sum(b["seconds"] for benches in results.values() for b in benches)

    row = {"flags": entry["flags"], "target": total_time}
    rows.append(row)

df = pd.DataFrame(rows)
print(df)
