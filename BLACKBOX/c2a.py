import json
from pathlib import Path


msa_path = ("MSA/msa_blackbox_outputs.json")
msc_path = ("MSC/msc_blackbox_outputs.json")
with open(msa_path) as f:
    msa = json.load(f)

with open(msc_path) as f:
    msc = json.load(f)

def decode(idx):
    return ("row", idx) if idx < 3 else ("col", idx - 3)

def map_inputs_msc_to_msa(a_msc, b_msc):
    """
    Given MSC inputs (a, b) where a in 0 to 5  (row r or column c) and b in 0 to 2  (index along Alice's line)
    return corresponding MSA inputs (a_msA, b_msA)
    """
    a_type, _ = decode(a_msc)
    if a_type == "row":
        return a_msc, 3 + b_msc   # Bob asks for column j
    else:  # column
        return a_msc, b_msc       # Bob asks for row i


# reduction verification code starts here 
all_ok = True
for a_msc in range(6):
    for b_msc in range(3):
        a_msa, b_msa = map_inputs_msc_to_msa(a_msc, b_msc)
        
        msa_key = f"{a_msa},{b_msa}"
        msc_key = f"{a_msc},{b_msc}"
        
        msa_outs = msa[msa_key]
        msc_outs = {(tuple(o["alice_vec"]), o["bob_bit"]) for o in msc[msc_key]}
        
        for out in msa_outs:
            alice_vec = out["alice_vec"]
            derived_bit = alice_vec[b_msc]  # intersection bit
            if (tuple(alice_vec), derived_bit) not in msc_outs:
                all_ok = False
                break  # this output invalidates reduction for this input

print("Reduction MS‑C to MS‑A valid for all inputs:", all_ok)
