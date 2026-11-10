"""Pool the two identical 48-qubit DD experiments and test certification."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import herding_cats as hc
import qats

a = json.loads(Path("qats_results/big_hardware_record.json").read_text())
b = json.loads(Path("qats_results/big48_precision_record.json").read_text())
for key in ("prep_qpy_b64", "qubits", "recipe", "seed"):
    assert a[key] == b[key], f"Cannot pool: {key} differs"
assert len(a["counts"]) == len(b["counts"])

def add_counts(left, right):
    out = dict(left)
    for bitstring, count in right.items():
        out[bitstring] = out.get(bitstring, 0) + count
    return out

counts = [add_counts(x, y) for x, y in zip(a["counts"], b["counts"])]
exp = hc.experiment_from_record(a, hc.fake_kingston())
result = exp.analyze(counts, bootstrap=1000, seed=10401)
lower = result.F - 2 * result.F_err
record = hc.experiment_record(exp, counts, result)
record.update({
    "where": "hardware-pooled",
    "source_job_ids": [a["job_id"], b["job_id"]],
    "certification_lower_bound": lower,
    "certified": lower > 0.5,
    "pooling_note": "Identical prep, qubits, recipe, seed, circuit order and random masks.",
})
Path("qats_results/big48_pooled_record.json").write_text(
    json.dumps(record, indent=2) + "\n"
)
print(result)
print("F - 2 sigma =", lower)
print("Certified:", lower > 0.5)
