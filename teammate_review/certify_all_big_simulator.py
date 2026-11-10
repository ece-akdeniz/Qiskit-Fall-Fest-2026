"""Certify every leaderboard big-cat tier on the official simulator snapshot."""
from dataclasses import asdict
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import herding_cats as hc
import qats

backend = hc.fake_kingston()
recipe = hc.Recipe(readout_mitigation=True, dd="XX", zne_factors=(1,))
rows = []
for index, n in enumerate((16, 24, 32, 40, 48, 64)):
    cat = qats.best_tree_cat(backend, n)
    assert cat is not None and hc.verify_cat(cat)
    seed = 11001 + index
    result = hc.measure_cat_quality(
        cat, qats.StableCatSimulator(backend, seed=seed), recipe,
        total_shots=100_000, seed=seed,
    )
    lower = result.F - 2 * result.F_err
    row = {
        "n": n, "where": "simulator", "seed": seed,
        "nominal_total_shots": 100_000,
        "qubits": hc.cat_qubits(cat), "recipe": asdict(recipe),
        "result": qats.result_dict(result),
        "certification_lower_bound": lower,
        "certified": lower > 0.5,
    }
    rows.append(row)
    Path("teammate_review/all_big_simulator_certification.json").write_text(
        json.dumps(rows, indent=2) + "\n"
    )
    print(f"N={n}: {result}; F-2sigma={lower:.6f}; certified={lower > 0.5}", flush=True)
