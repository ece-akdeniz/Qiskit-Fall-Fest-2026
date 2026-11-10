"""Screen recipes intended to reduce secret-seed sensitivity at fixed shots."""
from dataclasses import asdict
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import herding_cats as hc
import qats

backend = hc.fake_kingston()
cat = hc.load_circuit("qats_results/clean_cat.qpy")
seed = 10101
rows = []
for randomizations, factors in (
    (32, (1, 3, 5)),
    (64, (1, 3, 5)),
    (32, (1, 3, 5, 7)),
    (64, (1, 3, 5, 7)),
):
    recipe = hc.Recipe(
        readout_mitigation=True, gate_twirling=True,
        randomizations=randomizations, dd=None,
        zne_factors=factors, zne_extrapolator="exponential",
    )
    result = hc.measure_cat_quality(
        cat, qats.StableCatSimulator(backend, seed=seed), recipe,
        total_shots=40_000, seed=seed,
    )
    row = {
        "seed": seed, "nominal_total_shots": 40_000,
        "recipe": asdict(recipe), "result": qats.result_dict(result),
        "eps_star": hc.conservative_error(result),
    }
    rows.append(row)
    Path("teammate_review/robust_recipe_screen.json").write_text(
        json.dumps(rows, indent=2) + "\n"
    )
    print(randomizations, factors, result, "epsilon*=", row["eps_star"], flush=True)
