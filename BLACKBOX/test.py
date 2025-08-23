import json
from pathlib import Path


MSA_PATH = Path("MSA/msa_blackbox_outputs.json")
MSC_PATH = Path("MSC/msc_blackbox_outputs.json")  


PATTERNS = [
    (0,0,0), (0,0,1), (0,1,0), (0,1,1),
    (1,0,0), (1,0,1), (1,1,0), (1,1,1),
]
def pattern_id_binary(bits3):
    return PATTERNS.index(tuple(bits3))

def load_blackbox(path: Path):
    raw = json.loads(path.read_text())
    # keys are "a,b" -> convert to (int,int)
    return {tuple(map(int, k.split(","))): v for k, v in raw.items()}

def box_coords(b):  # (row, col) from 0..8
    return divmod(b, 3)

# known reduction tuple 
# fA: identity 
fA = {i: i for i in range(6)}

# fB: send each box to its row line in MSA
fB = {0:0, 1:0, 2:0, 3:1, 4:4, 5:1, 6:2, 7:2, 8:2}

# gA: for each (a,pattern) return the 3-bit pattern itself 
gA = {}
for a in range(6):
    gA[f"({a},0)"] = [0,0,0]
    gA[f"({a},1)"] = [0,0,1]
    gA[f"({a},2)"] = [0,1,0]
    gA[f"({a},3)"] = [0,1,1]
    gA[f"({a},4)"] = [1,0,0]
    gA[f"({a},5)"] = [1,0,1]
    gA[f"({a},6)"] = [1,1,0]
    gA[f"({a},7)"] = [1,1,1]

# gB: (box,pattern) -> intersection bit of that pattern at the box position
# (this table matches the one in your message; building it procedurally)
gB = {}
for box in range(9):
    r, c = box_coords(box)
    for p, vec in enumerate(PATTERNS):
        # if vec is an even pattern → row; odd → column
        if sum(vec) % 2 == 0:
            bit = vec[c]          # row: use column index
        else:
            bit = vec[r]          # column: use row index
        gB[f"({box},{p})"] = int(bit)


def gA_lookup(a, p):
    key = f"({a},{p})"
    if key in gA:      return list(gA[key])
    if (a,p) in gA:    return list(gA[(a,p)])
    raise KeyError(f"gA has no entry for (a={a}, p={p})")

def gB_lookup(box, p):
    key = f"({box},{p})"
    if key in gB:      return int(gB[key])
    if (box,p) in gB:  return int(gB[(box,p)])
    raise KeyError(f"gB has no entry for (box={box}, p={p})")


def evaluate_strategy(msa, msc, verbose=True, stop_on_first_fail=False):
    # collect the 18 legal MS-C pairs (box must lie on Alice's line)
    legal_pairs = [(a_c, box) for (a_c, box), outs in msc.items() if outs]
    legal_pairs.sort()
    if verbose:
        print(f"Found {len(legal_pairs)} legal MS-C question pairs.")

    wins = 0
    failures = []

    for a_c, box in legal_pairs:
        a_A = fA[a_c]
        b_A = fB[box]
        outs_a = msa.get((a_A, b_A), [])
        if not outs_a:
            failures.append({
                "pair": (a_c, box),
                "reason": "MS-A input illegal",
                "a_A": a_A, "b_A": b_A
            })
            if verbose:
                print(f"✗ (a_c={a_c}, box={box}) → (a_A={a_A}, b_A={b_A}) "
                      f"MS-A returned no outcomes")
            if stop_on_first_fail: break
            continue

        allowed = {(tuple(o["alice_vec"]), o["bob_bit"]) for o in msc[(a_c, box)]}

        ok_all = True
        # Every MS-A outcome must map into an allowed MS-C answer
        for out in outs_a:
            raw_line = out["alice_vec"]                 # 3-bit list from MS-A
            p = pattern_id_binary(raw_line)             # pattern id 0..7 (binary order)
            alice_after = gA_lookup(a_c, p)             # 3-bit line Alice will output
            bob_after   = gB_lookup(box, p)             # Bob's bit
            if (tuple(alice_after), bob_after) not in allowed:
                ok_all = False
                failures.append({
                    "pair": (a_c, box),
                    "reason": "mapped answer not allowed",
                    "raw_line": raw_line,
                    "pattern_id": p,
                    "alice_after": alice_after,
                    "bob_after": bob_after,
                    "one_allowed_example": next(iter(allowed)) if allowed else None
                })
                if verbose:
                    r, c = box_coords(box)
                    print(f"✗ (a_c={a_c}, box={box} @ r{r}c{c}) "
                          f"MS-A line {raw_line} (p={p}) → "
                          f"Alice {alice_after}, Bob {bob_after}  ∉ allowed")
                if stop_on_first_fail: break

        if ok_all:
            wins += 1
            if verbose:
                r, c = box_coords(box)
                print(f"✓ (a_c={a_c}, box={box} @ r{r}c{c}) "
                      f"passes all {len(outs_a)} MS-A outcomes")

        if stop_on_first_fail and not ok_all:
            break

    rate = wins / len(legal_pairs) if legal_pairs else 0.0
    if verbose:
        print("\nSUMMARY")
        print(f"  wins       : {wins}/{len(legal_pairs)}")
        print(f"  success    : {rate:.3f}")
        if failures:
            print(f"  failures   : {len(failures)} (showing first 3)")
            for f in failures[:3]:
                print("   -", f)
        else:
            print("  failures   : 0 (perfect)")

    return rate, failures


msa = load_blackbox(MSA_PATH)
msc = load_blackbox(MSC_PATH)

rate, fails = evaluate_strategy(msa, msc, verbose=True)


if rate < 1.0:
    print("\nASSERTION: This tuple is NOT a perfect reduction.")
else:
    print("\nASSERTION: Perfect reduction confirmed (100%).")
