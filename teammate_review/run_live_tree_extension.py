"""Run the shortest high-ESP live tree during the organizer extension."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qiskit_ibm_runtime import QiskitRuntimeService
import herding_cats as hc
import qats

real = QiskitRuntimeService().backend("ibm_kingston")
prep = qats.best_tree_cat(real, 12)
qubits = hc.cat_qubits(prep)
assert hc.verify_cat(prep, qubits)
report = hc.cat_report(prep, real)
print("Tree report:", report, flush=True)
hc.save_circuit(prep, "qats_results/live_tree_extension_cat.qpy")
recipe = hc.Recipe(
    readout_mitigation=True, gate_twirling=False, dd=None,
    zne_factors=(1, 5), zne_extrapolator="exponential",
)
final = hc.FinalJob(prep, recipe, real, total_shots=40_000, team_qubits=qubits)
estimate = hc.estimate_qpu_seconds(final.circuits, final.shots, real)
print(f"Prepared {len(final.circuits)} circuits x {final.shots} shots; estimate {estimate:.2f}s", flush=True)
assert estimate <= 15
job = qats.submit_once("clean_cat_extension_live_tree", final.circuits, final.shots, real)
final.save("qats_results/final_extension_live_tree_job.json", job_id=job.job_id())
print("Hardware job:", job.job_id(), flush=True)
counts = hc.HardwareRunner.counts_from_result(job.result())
record = final.record(job.job_id(), counts)
record["selection"] = report
qats.dump("hardware_extension_live_tree_record.json", record)
print("Hardware baseline:", record["baseline"]["result"], flush=True)
print("Hardware team:", record["team"]["result"], flush=True)
print("Error reduction:", record["error_reduction"], flush=True)
