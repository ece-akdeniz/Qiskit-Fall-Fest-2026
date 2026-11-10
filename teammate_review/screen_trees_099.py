"""Screen distinct 12-qubit trees before a held-out 0.99 verification."""

from dataclasses import asdict
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import herding_cats as hc
import qats


backend = hc.fake_kingston()
recipe = hc.Recipe(readout_mitigation=True)

# Generate trees under several defensible calibration thresholds.  Deduplicate
# by physical-qubit order so the simulation budget is spent on distinct cats.
candidates = {}
for max_readout in (0.02, 0.03, 0.05):
    for max_cz in (0.006, 0.01, 0.02):
        for min_t2 in (50e-6, 100e-6, 150e-6):
            for root in range(backend.num_qubits):
                cat = qats.make_tree_cat(
                    backend,
                    root,
                    12,
                    max_readout=max_readout,
                    max_cz=max_cz,
                    min_t2=min_t2,
                )
                if cat is None:
                    continue
                key = tuple(hc.cat_qubits(cat))
                candidates.setdefault(key, cat)

# ESP is a cheap pre-screen.  The saved clean cat is always included.
saved = hc.load_circuit("qats_results/clean_cat.qpy")
candidates.setdefault(tuple(hc.cat_qubits(saved)), saved)
ranked = sorted(
    candidates.items(),
    key=lambda item: hc.cat_report(item[1], backend)["ESP"],
    reverse=True,
)[:18]

rows = []
for index, (qubits, cat) in enumerate(ranked):
    assert hc.verify_cat(cat)
    result = hc.measure_cat_quality(
        cat,
        qats.StableCatSimulator(backend, seed=9301),
        recipe,
        total_shots=12_000,
        seed=9301,
    )
    report = hc.cat_report(cat, backend)
    row = {
        "rank": index + 1,
        "qubits": list(qubits),
        "report": report,
        "result": qats.result_dict(result),
        "eps_star": hc.conservative_error(result),
    }
    rows.append(row)
    Path("teammate_review/tree_screen_099.json").write_text(
        json.dumps(rows, indent=2) + "\n"
    )
    print(
        index + 1,
        f"F={result.F:.6f} +/- {result.F_err:.6f}",
        f"ESP={report['ESP']:.6f}",
        list(qubits),
        flush=True,
    )

best = max(rows, key=lambda row: (row["result"]["F"], -row["eps_star"]))
best_cat = candidates[tuple(best["qubits"])]
hc.save_circuit(best_cat, "teammate_review/tree_candidate_099.qpy")
Path("teammate_review/tree_candidate_099.json").write_text(
    json.dumps({"screen_seed": 9301, "recipe": asdict(recipe), **best}, indent=2)
    + "\n"
)
print("Selected screen candidate:", best["qubits"])
