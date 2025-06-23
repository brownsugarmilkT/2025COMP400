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

def cell_coords(b):          # 0..8  →  (row, col)
    return divmod(b, 3)

def bit_at(vec, j):
    return vec[j]

candidates = defaultdict(list)

for a in range(6):               # Alice input
    a_type, a_idx = decode(a)
    pool = EVEN_ROWS if a_type == "row" else ODD_COLS

    for b in range(9):           # Bob input 0..8
        r_b, c_b = cell_coords(b)

        # Does Bob’s cell lie on Alice’s line?
        on_line = (a_type == "row" and r_b == a_idx) or \
                  (a_type == "col" and c_b == a_idx)

        if not on_line:
            continue  # no admissible outputs → leave list empty

        for vec in pool:
            if a_type == "row":
                bob_bit = vec[c_b]
            else:  # column
                bob_bit = vec[r_b]

            candidates[(a, b)].append({
                "alice_type": a_type,
                "alice_vec":  vec,
                "bob_bit":    bob_bit,
            })

with open("msc_blackbox_outputs.json", "w") as f:
    json.dump(
        {f"{a},{b}": outs for (a, b), outs in sorted(candidates.items())},
        f, indent=4
    )


