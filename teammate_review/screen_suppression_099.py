"""Paired screen of DD and gate twirling on the selected clean-cat tree."""

from dataclasses import asdict
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import herding_cats as hc
import qats


backend = hc.fake_kingston()
cat = hc.load_circuit("qats_results/clean_cat.qpy")
rows = []
for label, dd, gate_twirling in (
    ("TREX + ZNE", None, False),
    ("DD + TREX + ZNE", "XX", False),
    ("TREX + twirling + ZNE", None, True),
    ("DD + TREX + twirling + ZNE", "XX", True),
):
    seed = 9501
    recipe = hc.Recipe(
        readout_mitigation=True,
        dd=dd,
        gate_twirling=gate_twirling,
        zne_factors=(1, 3, 5),
        zne_extrapolator="exponential",
    )
    result = hc.measure_cat_quality(
        cat,
        qats.StableCatSimulator(backend, seed=seed),
        recipe,
        total_shots=40_000,
        seed=seed,
    )
    row = {
        "label": label,
        "seed": seed,
        "recipe": asdict(recipe),
        "result": qats.result_dict(result),
        "eps_star": hc.conservative_error(result),
    }
    rows.append(row)
    Path("teammate_review/suppression_screen_099.json").write_text(
        json.dumps(rows, indent=2) + "\n"
    )
    print(label, result, flush=True)
