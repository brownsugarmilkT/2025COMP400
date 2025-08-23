import json
from collections import defaultdict

EVEN_ROWS = [
    [0,0,0], [0,1,1], [1,0,1], [1,1,0],
]
ODD_COLS = [
    [0,0,1], [0,1,0], [1,0,0], [1,1,1],
]

def decode(idx):
    return ("row", idx) if idx < 3 else ("col", idx - 3)

def cell_coords(b):          # 0..8 → (row, col)
    return divmod(b, 3)

candidates = {}

for a in range(6):                      # Alice line (row/col)
    a_type, a_idx = decode(a)
    pool = EVEN_ROWS if a_type == "row" else ODD_COLS

    for b in range(9):                  # Bob box 0..8
        r_b, c_b = divmod(b, 3)

        on_line = (a_type == "row" and r_b == a_idx) or \
                  (a_type == "col" and c_b == a_idx)

        outs = []
        if on_line:
            # 4 possible lines consistent with parity; Bob’s bit is the
            # intersection (col index for rows, row index for cols)
            for vec in pool:
                bob_bit = vec[c_b] if a_type == "row" else vec[r_b]
                outs.append({
                    "alice_type": a_type,
                    "alice_vec":  vec,
                    "bob_bit":    bob_bit,
                })
        # else: leave outs empty

        candidates[(a, b)] = outs

# write JSON
with open("msc_blackbox_outputs.json", "w") as f:
    json.dump(
        {f"{a},{b}": outs for (a, b), outs in sorted(candidates.items())},
        f, indent=2
    )

