"""Fresh grader-scale verification of the high-fidelity clean-cat recipe.

This is simulator-only.  It does not connect to IBM Quantum or submit hardware
jobs.  The seed was not used during circuit or recipe selection.
"""

from dataclasses import asdict
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import herding_cats as hc
import qats


backend = hc.fake_kingston()
cat = hc.load_circuit("qats_results/clean_cat.qpy")
recipe = hc.Recipe(
    readout_mitigation=True,
    gate_twirling=True,
    dd="XX",
    zne_factors=(1, 3, 5),
    zne_extrapolator="exponential",
)

assert hc.verify_cat(cat)
seed = 9201
result = hc.measure_cat_quality(
    cat,
    qats.StableCatSimulator(backend, seed=seed),
    recipe,
    total_shots=100_000,
    seed=seed,
)
record = {
    "seed": seed,
    "nominal_total_shots": 100_000,
    "recipe": asdict(recipe),
    "result": qats.result_dict(result),
    "target_reached": bool(result.F >= 0.99),
    "selection_note": "Seed 9201 was held out from all circuit and recipe selection.",
}
Path("teammate_review/verify_099.json").write_text(
    json.dumps(record, indent=2) + "\n"
)
print(result)
print("Fidelity target reached:", record["target_reached"])
