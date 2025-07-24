#!/usr/bin/env python3
"""
ctoa.py  – exhaustive MS-C → MS-A reduction search
with checkpoint / resume and persistent logging
"""
import json, itertools, atexit, signal, logging, argparse, math
from pathlib import Path
from typing   import Dict, List, Tuple

# ──────────────────────────  constants  ──────────────────────────
CHECKPOINT   = Path("checkpoint.json")
BEST_FILE    = Path("best.json")
LOG_FILE     = "search.log"
SAVE_EVERY   = 1_000_000          # iterations between checkpoints

# ──────────────────────────  logging  ──────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="a"),
        logging.StreamHandler()
    ],
)
log = logging.getLogger("search")

# ──────────────────────────  helper loaders  ────────────────────
def load_game(path: Path) -> Dict[Tuple[int,int], List[dict]]:
    raw = json.loads(path.read_text())
    return {tuple(map(int, k.split(","))): v for k, v in raw.items()}

def box_coords(box: int) -> Tuple[int, int]:
    return divmod(box, 3)

# ──────────────────────────  candidate generators  ──────────────
def generate_F_A():
    for mapping in itertools.product(range(6), repeat=6):      # 6^6
        yield lambda a, m=mapping: m[a]

def generate_F_B():
    for mapping in itertools.product(range(6), repeat=9):      # 6^9
        yield lambda box, m=mapping: m[box]

EVEN_ROWS = [(0,0,0),(0,1,1),(1,0,1),(1,1,0)]
ODD_COLS  = [(0,0,1),(0,1,0),(1,0,0),(1,1,1)]
PATTERNS  = EVEN_ROWS + ODD_COLS

def generate_G_A():
    tgt_even, tgt_odd = EVEN_ROWS, ODD_COLS
    for choices in itertools.product(range(4), repeat=8):      # 4^8
        def g_A(a_c, line, ch=choices):
            idx  = PATTERNS.index(tuple(line))
            pool = tgt_even if idx < 4 else tgt_odd
            return list(pool[ch[idx]])
        yield g_A

def generate_G_B():
    situations = [(ln,pos) for ln in range(6) for pos in range(3)]  # 18
    for bits in itertools.product([0,1], repeat=18):               # 2^18
        table = {s:b for s,b in zip(situations, bits)}
        def g_B(box_c, line, tbl=table):
            r,c       = box_coords(box_c)
            line_idx  = r if sum(line)%2==0 else 3+c
            pos       = c if line_idx < 3 else r
            return tbl[(line_idx,pos)]
        yield g_B

# ──────────────────────────  success-rate  ──────────────────────
def success_rate(msa, msc, f_A, f_B, g_A, g_B):
    for a_c in range(6):
        for box_c in range(9):
            outs_c = msc.get((a_c, box_c), [])
            if not outs_c:
                continue
            allowed = {(tuple(o["alice_vec"]), o["bob_bit"]) for o in outs_c}
            outs_a = msa[(f_A(a_c), f_B(box_c))]
            for out in outs_a:
                line = out["alice_vec"]
                if (tuple(g_A(a_c,line)), g_B(box_c,line)) not in allowed:
                    return 0.0           # early fail
    return 1.0                           # perfect

# ──────────────────────────  checkpoint helpers  ────────────────
def save_ckpt(state: dict):
    CHECKPOINT.write_text(json.dumps(state))
    log.info(f"checkpoint saved at {state['total_tested']:,}")

def load_ckpt():
    if CHECKPOINT.exists():
        return json.loads(CHECKPOINT.read_text())
    return None

# ── helper to expose internals of the lambdas ───────────────────
def dump_f_A(f_A):
    """Return list[6] showing where each a_C maps."""
    return [f_A(i) for i in range(6)]

def dump_g_B(g_B):
    """Return 36-bit int representing Bob’s table (row 0..2, col 0..2, orient 0/1)."""
    bits = 0
    for ln in range(6):
        for pos in range(3):
            for orient in (0, 1):
                # fake line pattern just to query the bit
                line = EVEN_ROWS[0] if orient == 0 else ODD_COLS[0]
                box  = ln*3 + pos if ln < 3 else pos*3 + (ln-3)
                bits = (bits << 1) | g_B(box, line)
    return bits

def dump_f_B(f_B):
    return [f_B(i) for i in range(9)]       # 9-entry vector

def dump_g_A(g_A):
    return [g_A(0, pat) for pat in PATTERNS]  # 8 outputs

# ──────────────────────────  main  ──────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--msa", type=Path, default="MSA/msa_blackbox_outputs.json")
    ap.add_argument("--msc", type=Path, default="MSC/msc_blackbox_outputs.json")
    args = ap.parse_args()

    msa = load_game(args.msa)
    msc = load_game(args.msc)

    FA, FB, GA, GB = generate_F_A(), generate_F_B(), generate_G_A(), generate_G_B()
    total_space = 6**6 * 6**9 * 4**8 * 2**18   # for % progress

    # ── resume or fresh start
    # ── resume or fresh start
    state = load_ckpt() or {}
    state.setdefault("total_tested", 0)
    state.setdefault("perfect_hits", 0)
    state.setdefault("best_score", 0.0)
    total_tested   = state["total_tested"]
    perfect_hits   = state["perfect_hits"]
    best_score     = state["best_score"]

    # rewind generators with islice skip
    product_iter = itertools.islice(
        itertools.product(FA, FB, GA, GB), total_tested, None
    )

    # ensure checkpoint on exit / SIGTERM
    def on_exit(*_):
        save_ckpt({"total_tested": total_tested,
                   "perfect_hits": perfect_hits,
                   "best_score"  : best_score})
    atexit.register(on_exit)
    signal.signal(signal.SIGTERM, on_exit)

    log.info(f"Starting search at iteration {total_tested:,}")

    # ── main loop
    try:
        for f_A, f_B, g_A, g_B in product_iter:
            total_tested += 1
            score = success_rate(msa, msc, f_A, f_B, g_A, g_B)

            if score == 1.0:
                perfect_hits += 1
                log.info(f"[+] PERFECT #{perfect_hits} at {total_tested:,}")
                # persist the perfect quadruple immediately
                BEST_FILE.write_text(json.dumps({"index": total_tested}))
            elif score > best_score:
                best_score = score

            if total_tested % SAVE_EVERY == 0:
                save_ckpt({"total_tested": total_tested,
                           "perfect_hits": perfect_hits,
                           "best_score"  : best_score})
                pct = 100 * total_tested / total_space
                fA_index = total_tested // (6**9 * 4**8 * 2**18)
                log.info(f"[{total_tested:,}]  {pct:.3e}%  best={best_score:.3f}"
                         f"... fA={dump_f_A(f_A)} "
                            f"fB={dump_f_B(f_B)} "
                            f"gA={dump_g_A(g_A)} "
                            f"gB_bits={dump_g_B(g_B):036b}")

    except KeyboardInterrupt:
        log.warning("Interrupted by user – saving checkpoint and exiting.")
        on_exit()

if __name__ == "__main__":
    main()
