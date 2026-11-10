"""Final unseen-seed verification for the 0.99 clean-cat target."""

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
    dd=None,
    zne_factors=(1, 3, 5),
    zne_extrapolator="exponential",
)
seed = 9601
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
    "cat_qpy": "qats_results/clean_cat.qpy",
    "qubits": hc.cat_qubits(cat),
    "report": hc.cat_report(cat, backend),
    "recipe": asdict(recipe),
    "result": qats.result_dict(result),
    "target_reached": bool(result.F >= 0.99),
    "selection_note": "Seed 9601 was held out from all layout, recipe and suppression screening.",
}
Path("teammate_review/final_verify_099.json").write_text(
    json.dumps(record, indent=2) + "\n"
)
print(result)
print("Fidelity target reached:", record["target_reached"])
