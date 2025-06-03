import json
from collections import defaultdict
import csv

# even parity rows - Alice
rows = [
    [0, 0, 0],
    [0, 1, 1],
    [1, 1, 0],
    [1, 0, 1],
]

# odd parity columns - Bob
cols = [
    [0, 0, 1],
    [0, 1, 0],
    [1, 0, 0],
    [1, 1, 1],
]

# To store valid outputs for each input (a, b) where a, b are indexed on {1, 2, 3}
f_candidates = defaultdict(list)

for a in [1, 2, 3]:  # Alice input (row)
    for b in [1, 2, 3]:  # Bob input (column)
        for row in rows:
            for col in cols:
                if row[b - 1] == col[a - 1]:
                    f_candidates[(a, b)].append({
                        "row": row,
                        "col": col
                    })


f_candidates_json = {
    f"{a},{b}": outputs for (a, b), outputs in sorted(f_candidates.items())
}

with open("msb_blackbox_outputs.json", "w") as f:
    json.dump(f_candidates_json, f, indent=4)

print("Saved to msb_blackbox_outputs.json")

