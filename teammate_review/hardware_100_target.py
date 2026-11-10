"""Combine Defne's best live layout with Qats' best simulator recipe."""

import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import herding_cats as hc
import qats
from qiskit_ibm_runtime import QiskitRuntimeService


record = json.loads(
    subprocess.check_output(
        ["git", "show", "origin/defne:hardware_record.json"], text=True
    )
)
qubits = record["team"]["qubits"]
fake = hc.fake_kingston()
prep = hc.experiment_from_record(record["team"], fake).prep
assert hc.verify_cat(prep, qubits)

recipe = hc.Recipe(
    readout_mitigation=True,
    gate_twirling=True,
    dd=None,
    zne_factors=(1, 3, 5),
    zne_extrapolator="exponential",
)
trial = hc.measure_cat_quality(
    prep,
    qats.StableCatSimulator(fake, seed=9801),
    recipe,
    total_shots=12_000,
    qubits=qubits,
    seed=9801,
)
qats.dump("defne_layout_twirling_rehearsal.json", qats.result_dict(trial))
print("Simulator rehearsal:", trial, flush=True)
assert trial.F > 0.5

service = QiskitRuntimeService()
real = service.backend("ibm_kingston")
final = hc.FinalJob(
    prep,
    recipe,
    real,
    total_shots=40_000,
    team_qubits=qubits,
)
estimate = hc.estimate_qpu_seconds(final.circuits, final.shots, real)
print(
    f"Prepared {len(final.circuits)} circuits x {final.shots} shots; "
    f"estimated QPU time {estimate:.1f}s",
    flush=True,
)
assert estimate <= 15

job = qats.submit_once(
    "clean_cat_defne_layout_twirling", final.circuits, final.shots, real
)
final.save("qats_results/final_defne_layout_twirling_job.json", job_id=job.job_id())
print("Hardware job:", job.job_id(), flush=True)
counts = hc.HardwareRunner.counts_from_result(job.result())
hardware_record = final.record(job.job_id(), counts)
qats.dump("hardware_defne_layout_twirling_record.json", hardware_record)
print("Hardware baseline:", hardware_record["baseline"]["result"], flush=True)
print("Hardware team:", hardware_record["team"]["result"], flush=True)
print("Error reduction:", hardware_record["error_reduction"], flush=True)
