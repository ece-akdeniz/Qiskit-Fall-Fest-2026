"""Independent 100,000-shot verification of the combined 1.0 simulator target."""

from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import herding_cats as hc
import qats


record = json.loads(
    subprocess.check_output(
        ["git", "show", "origin/defne:hardware_record.json"], text=True
    )
)
backend = hc.fake_kingston()
qubits = record["team"]["qubits"]
prep = hc.experiment_from_record(record["team"], backend).prep
recipe = hc.Recipe(
    readout_mitigation=True,
    gate_twirling=True,
    dd=None,
    zne_factors=(1, 3, 5),
    zne_extrapolator="exponential",
)
seed = 9901
result = hc.measure_cat_quality(
    prep,
    qats.StableCatSimulator(backend, seed=seed),
    recipe,
    total_shots=100_000,
    qubits=qubits,
    seed=seed,
)
output = {
    "seed": seed,
    "nominal_total_shots": 100_000,
    "source_layout": "Defne hardware record, branch e957e71",
    "qubits": qubits,
    "recipe": asdict(recipe),
    "result": qats.result_dict(result),
    "target_reached": bool(result.F >= 1.0),
}
Path("teammate_review/simulation_100_target.json").write_text(
    json.dumps(output, indent=2) + "\n"
)
print(result)
print("Simulation 1.0 target reached:", output["target_reached"])
