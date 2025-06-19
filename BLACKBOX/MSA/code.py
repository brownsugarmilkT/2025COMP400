import json
from collections import defaultdict

EVEN_LINES = [               
    [0,0,0], [0,1,1],
    [1,0,1], [1,1,0],
]
ODD_LINES  = [                
    [0,0,1], [0,1,0],
    [1,0,0], [1,1,1],
]

def decode(i):
    return ("row", i) if i < 3 else ("col", i-3)

def pool(t):                  # row > even , col > odd
    return EVEN_LINES if t == "row" else ODD_LINES

def overlap_ok(at, ai, av, bt, bi, bv):
    if at == "row" and bt == "col":
        return av[bi] == bv[ai]
    if at == "col" and bt == "row":
        return av[bi] == bv[ai]
    if at == bt and ai == bi:           # same line
        return av == bv
    return True                        # parallel lines (no overlap)

cand = defaultdict(list)
for a in range(6):
    at, ai = decode(a)
    for b in range(6):
        bt, bi = decode(b)
        for av in pool(at):
            for bv in pool(bt):
                if overlap_ok(at, ai, av, bt, bi, bv):
                    cand[(a,b)].append({
                        "alice_type": at, "alice_vec": av,
                        "bob_type": bt,   "bob_vec":  bv,
                    })

with open("msa_blackbox_outputs.json", "w") as f:
    json.dump({f"{a},{b}":v for (a,b),v in sorted(cand.items())}, f, indent=4)

