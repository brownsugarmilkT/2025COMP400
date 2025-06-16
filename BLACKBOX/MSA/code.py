import json
from collections import defaultdict

# Even - Alice 
alice = [
    [0, 0, 0],
    [0, 1, 1],
    [1, 0, 1],
    [1, 1, 0],
]

# Odd - Bob
bob = [
    [0, 0, 1],
    [0, 1, 0],
    [1, 0, 0],
    [1, 1, 1],
]


def decode(input):
    if input< 3:
        return ("row", input)       # rows - 0,1,2
    else:
        return ("col", input - 3)   # cols - 0,1,2 (encoded as 3,4,5)


f_candidates = defaultdict(list)

for a in range(6):     # Alice input 
    a_type, a_idx = decode(a)
    if a_type == "row" or a_type == "col":
        poolA = alice
    else:
        []

    
    for b in range(6): # Bob input
        b_type, b_idx = decode(b)
        poolB = bob                                      
        for vecA in poolA:
            for vecB in poolB:
                overlap = True

                if a_type == "row" and b_type == "col":
                    overlap = vecA[b_idx] == vecB[a_idx]

                elif a_type == "col" and b_type == "row":
                    overlap = vecA[b_idx] == vecB[a_idx]

                elif a_type == "row" and b_type == "row":
                    # overlap only if same row index
                    if a_idx == b_idx:
                        overlap = vecA == vecB

                elif a_type == "col" and b_type == "col":
                    # overlap only if same column index
                    if a_idx == b_idx:
                        overlap = vecA == vecB

                if overlap:
                    f_candidates[(a, b)].append({
                        "alice_type": a_type,
                        "vecA": vecA,
                        "bob_type": b_type,
                        "vecB": vecB,
                    })


f_candidates_json = {
    f"{a},{b}": outputs for (a, b), outputs in sorted(f_candidates.items())
}

file_path = "msa_blackbox_outputs.json"
with open(file_path, "w") as f:
    json.dump(f_candidates_json, f, indent=4)