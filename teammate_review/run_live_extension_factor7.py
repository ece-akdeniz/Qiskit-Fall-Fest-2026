"""Test stronger two-point ZNE on the best live middle-grown layout."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qiskit_ibm_runtime import QiskitRuntimeService
import herding_cats as hc
import qats

choice = json.loads(Path("qats_results/live_extension_choice.json").read_text())
prep = hc.load_circuit("qats_results/live_extension_cat.qpy")
qubits = choice["qubits"]
recipe = hc.Recipe(
    readout_mitigation=True, gate_twirling=False, dd=None,
    zne_factors=(1, 7), zne_extrapolator="exponential",
)
real = QiskitRuntimeService().backend("ibm_kingston")
final = hc.FinalJob(prep, recipe, real, total_shots=40_000, team_qubits=qubits)
estimate = hc.estimate_qpu_seconds(final.circuits, final.shots, real)
print(f"Prepared {len(final.circuits)} circuits x {final.shots} shots; estimate {estimate:.2f}s", flush=True)
assert estimate <= 15
job = qats.submit_once("clean_cat_extension_live_factor7", final.circuits, final.shots, real)
final.save("qats_results/final_extension_live_factor7_job.json", job_id=job.job_id())
print("Hardware job:", job.job_id(), flush=True)
counts = hc.HardwareRunner.counts_from_result(job.result())
record = final.record(job.job_id(), counts)
record["selection"] = choice
qats.dump("hardware_extension_live_factor7_record.json", record)
print("Hardware baseline:", record["baseline"]["result"], flush=True)
print("Hardware team:", record["team"]["result"], flush=True)
print("Error reduction:", record["error_reduction"], flush=True)
