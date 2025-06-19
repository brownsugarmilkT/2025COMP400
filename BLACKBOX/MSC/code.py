import json
from collections import defaultdict

EVEN_ROWS = [
    [0, 0, 0],
    [0, 1, 1],
    [1, 0, 1],
    [1, 1, 0],
]

ODD_COLS = [
    [0, 0, 1],
    [0, 1, 0],
    [1, 0, 0],
    [1, 1, 1],
]

def decode(idx):
    return ("row", idx) if idx < 3 else ("col", idx - 3)

def bit_at(vec, j):
    return vec[j]

candidates = defaultdict(list)

for a in range(6):                        # Alice input 0-5
    a_type, _ = decode(a)
    pool = EVEN_ROWS if a_type == "row" else ODD_COLS

    for b in range(3):                    # Bob input 0-2 
        for line in pool:
            candidates[(a, b)].append({
                "alice_type": a_type,
                "alice_vec": line,
                "bob_bit":    bit_at(line, b),
            })

with open("msc_blackbox_outputs.json", "w") as f:
    json.dump(
        {f"{a},{b}": outs for (a, b), outs in sorted(candidates.items())},
        f, indent=4
    )


