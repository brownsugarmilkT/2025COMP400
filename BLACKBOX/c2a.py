import json
from pathlib import Path

msa_path = Path("MSA/msa_blackbox_outputs.json")
msc_path = Path("MSC/msc_blackbox_outputs.json")   

msa = json.loads(msa_path.read_text())
msc = json.loads(msc_path.read_text())


def decode_line(idx):
    return ("row", idx) if idx < 3 else ("col", idx - 3)

def cell_coords(box):          # 0..8  →  (row, col)
    return divmod(box, 3)


def map_inputs_msc_to_msa(a_msc, b_msc):

    a_type, a_idx = decode_line(a_msc)
    r_b, c_b      = cell_coords(b_msc)

    if a_type == "row":                    # Alice has row a_idx
        return a_msc, 3 + c_b              # Bob queries *column* c_b in MS-A
    else:                                  # Alice has column a_idx
        return a_msc, r_b                  # Bob queries *row*    r_b  in MS-A

legal_pairs = 0
working_pairs = 0

for a_msc in range(6):
    for b_msc in range(9):
        msc_key = f"{a_msc},{b_msc}"
        if not msc[msc_key]:               # empty list ⇒ illegal pair
            continue

        legal_pairs += 1

        a_msa, b_msa = map_inputs_msc_to_msa(a_msc, b_msc)
        msa_key = f"{a_msa},{b_msa}"

        msa_outs = msa[msa_key]
        msc_outs = {(tuple(o["alice_vec"]), o["bob_bit"]) for o in msc[msc_key]}

        ok = True
        for out in msa_outs:
            alice_vec  = out["alice_vec"]
            r_b, c_b   = cell_coords(b_msc)
            derived_bit = alice_vec[c_b] if a_msc < 3 else alice_vec[r_b]

            if (tuple(alice_vec), derived_bit) not in msc_outs:
                ok = False
                break

        working_pairs += ok


success = 100 * working_pairs / legal_pairs if legal_pairs else 0
print(f"Legal input pairs   : {legal_pairs}")
print(f"Pairs where reduction works: {working_pairs}")
print(f"Success rate        : {success:.1f}%")
