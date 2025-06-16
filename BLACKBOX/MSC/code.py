import json
from collections import defaultdict

# Even ALice
alice = [
    [0, 0, 0],
    [0, 1, 1],
    [1, 0, 1],
    [1, 1, 0],
]

def decode_alice(i): # 0-2 rows 3-5 columns 
    return ("row", i) if i < 3 else ("col", i - 3)

def intersection_bit(typeA, vecA, bob_index):
    return vecA[bob_index]

f_candidates = defaultdict(list)

for a in range(6):          # Alice input 0–5
    typeA, _ = decode_alice(a)

    for b in range(3):      # Bob input 0–2 
        for vecA in alice:
            bob = intersection_bit(typeA, vecA, b)
            f_candidates[(a, b)].append({
                "alice_type": typeA,
                "alice_vec": vecA,
                "bob_bit": bob,
            })


f_candidates_json = {
    f"{a},{b}": outs for (a, b), outs in sorted(f_candidates.items())
}

with open("msc_blackbox_outputs.json", "w") as f:
    json.dump(f_candidates_json, f, indent=4)