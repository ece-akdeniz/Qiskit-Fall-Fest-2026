"""Independent higher-shot check of the statistically inconclusive 64-qubit cat."""
from pathlib import Path
from dataclasses import asdict
import json
import herding_cats as hc
import qats

backend = hc.fake_kingston()
cat = qats.best_tree_cat(backend, 64)
assert cat is not None and hc.verify_cat(cat)
recipe = hc.Recipe(dd="XX", readout_mitigation=True)
exp = hc.build_cat_experiment(cat, backend, recipe, seed=2903)
result = exp.run(qats.StableCatSimulator(backend, seed=2903), total_shots=32_000)
hc.save_circuit(cat, "qats_results/big64_sim_cat.qpy")
qats.dump("big64_independent_record.json", hc.biggest_cat_record(
    exp, exp.last_counts, result, where="simulator"))
print("Independent 64-qubit check, 32k shots:", result, flush=True)

if result.certified:
    from qiskit_ibm_runtime import QiskitRuntimeService
    service = QiskitRuntimeService()
    real = service.backend("ibm_kingston")
    live = qats.best_tree_cat(real, 64)
    if live is None:
        raise RuntimeError("No 64-qubit live tree under the calibration thresholds")
    assert hc.verify_cat(live)
    hc.save_circuit(live, "qats_results/big64_live_cat.qpy")
    live_exp = hc.build_cat_experiment(live, real, recipe, seed=2903)
    shots = live_exp.shots_per_circuit(40_000)
    qats.dump("big64_hardware_spec.json", {"n":64, "seed":2903,
        "recipe":asdict(recipe), "shots":shots})
    job = qats.submit_once("big_cat_64", live_exp.circuits, shots, real)
    print("Waiting for 64-qubit hardware check:", job.job_id(), flush=True)
    counts = hc.HardwareRunner.counts_from_result(job.result())
    live_result = live_exp.analyze(counts)
    qats.dump("big64_hardware_record.json", hc.biggest_cat_record(
        live_exp, counts, live_result, where="hardware", job_id=job.job_id()))
    print("64-qubit hardware:", live_result, flush=True)
else:
    print("64 qubits remains uncertified; no extra hardware job submitted.", flush=True)
