import json
from pathlib import Path


msa_path = ("MSA/msa_blackbox_outputs.json")
msb_path = ("MSB/msb_blackbox_outputs.json")
with open(msa_path) as f:
    msa = json.load(f)

with open(msb_path) as f:
    msb = json.load(f)

def map_inputs_msb_to_msa(a_msb, b_msb):
    """
    Given MSB inputs (a, b) where a in 0 to 2 (row r) and b in 0 to 2() column c)
    return corresponding MSA inputs 
    """
    # Alice row index 0-2 stays same
    # Bob column index 0-2 gets encoded as 3+col in MSA
    return a_msb, 3 + b_msb

all_ok=True
for a_msb in range(3):
    for b_msb in range(3):
        a_msa, b_msa = map_inputs_msb_to_msa(a_msb, b_msb)

        msa_key=f"{a_msa},{b_msa}"
        msb_key=f"{a_msb},{b_msb}"

        msa_outs=msa[msa_key]
        msb_set={(tuple(o["alice_vec"]), tuple(o["bob_vec"])) for o in msb[msb_key]}

        for out in msa_outs:
            alice_vec=out["alice_vec"]
            bob_vec=out["bob_vec"]
            if (tuple(alice_vec), tuple(bob_vec)) not in msb_set:
                all_ok=False
                break
        if not all_ok:
            break
    if not all_ok:
        break

print("Reduction MSB to MSA valid for all inputs:", all_ok) # FIX, Currently it's false, it should be True according to paper. 