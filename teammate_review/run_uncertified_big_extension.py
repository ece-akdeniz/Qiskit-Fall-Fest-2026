"""Submit fresh 48- and 64-qubit hardware attempts during the extension."""
from dataclasses import asdict
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qiskit_ibm_runtime import QiskitRuntimeService
import herding_cats as hc
import qats

real = QiskitRuntimeService().backend("ibm_kingston")
recipe = hc.Recipe(readout_mitigation=True, dd="XX", zne_factors=(1,))
pending = []
for n, seed, nominal in ((48, 4803, 48_000), (64, 6403, 36_000)):
    prep = qats.best_tree_cat(real, n)
    assert prep is not None and hc.verify_cat(prep)
    qubits = hc.cat_qubits(prep)
    hc.save_circuit(prep, f"qats_results/big{n}_extension_cat.qpy")
    exp = hc.build_cat_experiment(prep, real, recipe, qubits=qubits, seed=seed)
    shots = exp.shots_per_circuit(nominal)
    while hc.estimate_qpu_seconds(exp.circuits, shots, real) > 15:
        shots -= 1
    estimate = hc.estimate_qpu_seconds(exp.circuits, shots, real)
    print(f"N={n}: {len(exp.circuits)} circuits x {shots}; estimate {estimate:.2f}s", flush=True)
    job = qats.submit_once(f"big_cat_{n}_extension", exp.circuits, shots, real)
    qats.dump(f"big{n}_extension_spec.json", {
        "job_id": job.job_id(), "recipe": asdict(recipe), "seed": seed,
        "shots": shots, "qubits": qubits, "estimated_seconds": estimate,
    })
    print(f"Submitted N={n}: {job.job_id()}", flush=True)
    pending.append((n, exp, job))

for n, exp, job in pending:
    counts = hc.HardwareRunner.counts_from_result(job.result())
    result = exp.analyze(counts, bootstrap=1000, seed=12000 + n)
    record = hc.biggest_cat_record(exp, counts, result, where="hardware", job_id=job.job_id())
    qats.dump(f"big{n}_extension_record.json", record)
    print(f"N={n}: {result}; F-2sigma={result.F - 2*result.F_err:.6f}", flush=True)
