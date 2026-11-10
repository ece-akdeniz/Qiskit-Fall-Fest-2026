"""Held-out full-budget verification for the robust-recipe screen winner."""
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
    readout_mitigation=True, gate_twirling=True, randomizations=64,
    dd=None, zne_factors=(1, 3, 5, 7), zne_extrapolator="exponential",
)
seed = 10201
result = hc.measure_cat_quality(
    cat, qats.StableCatSimulator(backend, seed=seed), recipe,
    total_shots=100_000, seed=seed,
)
payload = {
    "seed": seed, "nominal_total_shots": 100_000,
    "recipe": asdict(recipe), "result": qats.result_dict(result),
    "eps_star": hc.conservative_error(result),
    "target_reached": result.F >= 1.0,
}
Path("teammate_review/verify_robust_recipe_100.json").write_text(
    json.dumps(payload, indent=2) + "\n"
)
print(result)
print("epsilon*:", payload["eps_star"])
print("Simulation 1.0 target reached:", payload["target_reached"])
