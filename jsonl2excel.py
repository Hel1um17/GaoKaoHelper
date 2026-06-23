import pandas as pd
import json

input_file = "result.jsonl"
output_file = "result.xlsx"

rows = []

with open(input_file, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            rows.append(json.loads(line))

df = pd.DataFrame(rows)
df.to_excel(output_file, index=False)

print("done")