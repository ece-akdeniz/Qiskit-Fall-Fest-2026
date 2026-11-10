"""Held-out, grader-scale validation of the screened tree candidate."""

from dataclasses import asdict
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import herding_cats as hc
import qats


backend = hc.fake_kingston()
cat = hc.load_circuit("teammate_review/tree_candidate_099.qpy")
seed = 9401
base = dict(
    readout_mitigation=True,
    gate_twirling=False,
    dd=None,
    zne_factors=(1, 3, 5),
)

# Exponential and quadratic extrapolation use exactly the same circuits.  Run
# those circuits once, then analyze the same counts both ways for a paired test.
quadratic_recipe = hc.Recipe(**base, zne_extrapolator="quadratic")
quadratic_exp = hc.build_cat_experiment(cat, backend, quadratic_recipe, seed=seed)
quadratic = quadratic_exp.run(
    qats.StableCatSimulator(backend, seed=seed), total_shots=100_000
)
counts = quadratic_exp.last_counts

exponential_recipe = hc.Recipe(**base, zne_extrapolator="exponential")
exponential_exp = hc.build_cat_experiment(cat, backend, exponential_recipe, seed=seed)
assert len(exponential_exp.circuits) == len(quadratic_exp.circuits)
exponential = exponential_exp.analyze(counts)

record = {
    "seed": seed,
    "nominal_total_shots": 100_000,
    "qubits": hc.cat_qubits(cat),
    "report": hc.cat_report(cat, backend),
    "results": {
        "quadratic": qats.result_dict(quadratic),
        "exponential": qats.result_dict(exponential),
    },
    "recipes": {
        "quadratic": asdict(quadratic_recipe),
        "exponential": asdict(exponential_recipe),
    },
    "target_reached": bool(max(quadratic.F, exponential.F) >= 0.99),
    "selection_note": "Seed 9401 was held out from tree and recipe screening.",
}
Path("teammate_review/validate_tree_099.json").write_text(
    json.dumps(record, indent=2) + "\n"
)
print("quadratic:", quadratic)
print("exponential:", exponential)
print("Fidelity target reached:", record["target_reached"])
