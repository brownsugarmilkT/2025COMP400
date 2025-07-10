import json, itertools, argparse
from pathlib import Path
from typing import Dict, List, Tuple

#  Load lookup table
def load_game(path: Path) -> Dict[Tuple[int,int], List[dict]]:
    raw = json.loads(path.read_text())
    return {tuple(map(int, k.split(","))): v for k, v in raw.items()}


#  1. Geometry helpers  
def decode_line(idx: int) -> Tuple[str, int]:
    """0–2 → ('row',r); 3–5 → ('col',c)."""
    return ("row", idx) if idx < 3 else ("col", idx - 3)

def box_coords(box: int) -> Tuple[int, int]:
    """0–8 → (row, col)."""
    return divmod(box, 3)


#  2. Candidate-set generators   

def generate_F_A():
    """All 6^6 deterministic maps a_C∈{0..5} → a_A∈{0..5}."""
    for mapping in itertools.product(range(6), repeat=6):
        yield lambda a, m=mapping: m[a]

def generate_F_B():
    """All 6^9 deterministic maps box∈{0..8} → line∈{0..5}."""
    for mapping in itertools.product(range(6), repeat=9):
        yield lambda box, m=mapping: m[box]


EVEN_ROWS = [(0,0,0), (0,1,1), (1,0,1), (1,1,0)]
ODD_COLS  = [(0,0,1), (0,1,0), (1,0,0), (1,1,1)]
PATTERNS  = EVEN_ROWS + ODD_COLS                     

def generate_G_A():
    """Parity-preserving maps on the 8 patterns; outputs must respect parity."""
    # Build lookup tables: index 0-3 → even, 4-7 → odd
    targets_even = EVEN_ROWS
    targets_odd  = ODD_COLS
    

    #For an even-row input (IDs 0-3) Alice may output any of the 4 even 3-bit rows → 4 choices
    #For an odd-column input (IDs 4-7) she may output any of the 4 odd columns → 4 choices

    for choices in itertools.product(range(4), repeat=8):   # 4^8 Instead of 24^8
        def g_A(a_c, line, ch=choices):
            idx = PATTERNS.index(tuple(line))
            return list((targets_even if idx < 4 else targets_odd)[ch[idx]])
        yield g_A

# There are 6 distinct lines in the board (rows 0-2, cols 0-2)
# On each line Bob’s box can occupy 3 positions
# For each of those 18 cases Bob’s deterministic function can output either 0 or 1 therefore 2^18
def generate_G_B():
    """All 2^18 local bit-maps: (line_idx, pos) → {0,1}."""
    situations = [(ln, pos) for ln in range(6) for pos in range(3)]  # 18
    for bits in itertools.product([0,1], repeat=18):
        table = {s: b for s, b in zip(situations, bits)}
        def g_B(box_c, line):
            r, c = box_coords(box_c)
            line_idx = r if len(line)==3 and line.count(1)%2==0 else 3+c
            pos = c if line_idx < 3 else r
            return table[(line_idx, pos)]
        yield g_B


# ##### 24^ 8 and 2^36. Take way too long imo. 

# def generate_G_A_v24():
#     """
#     Parity *not* fixed: for each of the 8 parity patterns that Alice may see
#     (4 even-row patterns + 4 odd-col patterns) she may output **any** of the
#     24 legal 3-bit lines (3 rows × 4 even patterns  +  3 cols × 4 odd patterns).

#     Total deterministic maps: 24^8.
#     """
#     # Build the full set of 24 legal lines (row/col index is baked in)
#     LINES_24 = []
#     for idx in range(3):
#         for pat in EVEN_ROWS:              # rows keep even patterns
#             LINES_24.append(("row", idx, pat))
#     for idx in range(3):
#         for pat in ODD_COLS:               # cols keep odd patterns
#             LINES_24.append(("col", idx, pat))

#     # PATTERNS is the list of the 8 parity patterns we already use
#     for choices in itertools.product(range(24), repeat=8):   # 24^8 combos
#         def g_A(a_c, line, ch=choices):
#             # Identify which of the 8 input patterns we are seeing
#             pat_id = PATTERNS.index(tuple(line))
#             _, _, out_vec = LINES_24[ch[pat_id]]
#             return list(out_vec)           # return the 3-bit vector
#         yield g_A



# def generate_G_B_v36():
#     """
#     Bob's post-processor may depend on
#       • which *line index* he queried in MS-A   (0-5)
#       • the *position* of his box on that line  (0-2)
#       • and a 1-bit flag that tells whether the line is an even-row
#         or an odd-column (orient_flag ∈ {0,1})

#     That makes 6 × 3 × 2 = 36 local situations, hence 2^36 deterministic
#     bit-maps to enumerate.
#     """
#     situations = [
#         (line_idx, pos, orient_flag)
#         for line_idx in range(6)           # 0..2 rows, 3..5 cols
#         for pos in range(3)                # position on that line
#         for orient_flag in (0, 1)          # 0 = even-row, 1 = odd-col
#     ]                                       # |situations| = 36

#     for bits in itertools.product([0, 1], repeat=36):        # 2^36
#         table = {s: b for s, b in zip(situations, bits)}

#         def g_B(box_c, line, tbl=table):
#             r, c = box_coords(box_c)
#             line_idx = r if sum(line) % 2 == 0 else 3 + c   # even→row, odd→col
#             pos      = c if line_idx < 3 else r
#             orient   = 0 if sum(line) % 2 == 0 else 1
#             return tbl[(line_idx, pos, orient)]
#         yield g_B



#  3. Success-rate evaluator                                         #
def success_rate(msa, msc, f_A, f_B, g_A, g_B):
    legal = wins = 0
    for a_c in range(6):
        for box_c in range(9):
            outs_c = msc.get((a_c, box_c), [])
            if not outs_c:              # illegal question
                continue
            legal += 1

            a_A = f_A(a_c)
            b_A = f_B(box_c)
            outs_a = msa[(a_A, b_A)]

            allowed = {(tuple(o["alice_vec"]), o["bob_bit"]) for o in outs_c}
            ok = True
            for out in outs_a:
                alice_vec = out["alice_vec"]
                alice_c   = g_A(a_c, alice_vec)
                bob_c     = g_B(box_c, alice_vec)
                if (tuple(alice_c), bob_c) not in allowed:
                    ok = False
                    break
            wins += ok
            if not ok:      # early bail-out
                return 0.0
    return wins / legal if legal else 0.0


#  4. Main exhaustive loop                                           


# stats
total_tested   = 0
perfect_hits   = 0
best_score     = -1.0
best_quadruple = None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--msa", required=True, type=Path)
    ap.add_argument("--msc", required=True, type=Path)
    args = ap.parse_args()

    msa = load_game(args.msa)
    msc = load_game(args.msc)

    # Enumerators
    FA  = generate_F_A()
    FB  = generate_F_B()
    GA  = generate_G_A()
    GB  = generate_G_B()

    for (f_A, f_B, g_A, g_B) in itertools.product(FA, FB, GA, GB):
        total_tested += 1
        score = success_rate(msa, msc, f_A, f_B, g_A, g_B)

        # keep ‘best so far’
        if score > best_score:
            best_score     = score
            best_quadruple = (f_A, f_B, g_A, g_B)

        if score == 1.0:
            perfect_hits += 1
            print(f"[+] PERFECT #{perfect_hits}  after {total_tested:,} tests")

        # every 1 000 000 iterations, print a heartbeat
        if total_tested % 1_000_000 == 0:
            pct = 100 * total_tested / (6**6 * 6**9 * 4**8 * 2**18)
            print(f"[{total_tested:,}]  ~{pct:.6e}%  best={best_score:.3f}")

    print("\n========== SUMMARY ==========")
    print(f"total tested  : {total_tested:,}")
    print(f"perfect hits  : {perfect_hits}")
    print(f"best score    : {best_score:.3f}")
    if best_quadruple:
        print("best quadruple (object ids):",
            *map(id, best_quadruple))

if __name__ == "__main__":
    main()
