"""One predeclared precision check, then a simulator-validated smaller fallback."""
from pathlib import Path
from dataclasses import asdict
import json
from qiskit_ibm_runtime import QiskitRuntimeService
import herding_cats as hc
import qats

service = QiskitRuntimeService()
real = service.backend("ibm_kingston")
fake = hc.fake_kingston()
spec = json.loads(Path("qats_results/big_hardware_spec.json").read_text())
recipe = hc.Recipe(**spec["recipe"])
prep = hc.load_circuit("big_live_cat.qpy")
assert hc.verify_cat(prep)
exp = hc.build_cat_experiment(prep, real, recipe, seed=spec["seed"])
shots = exp.shots_per_circuit(48_000)
job = qats.submit_once("big_cat_48_precision", exp.circuits, shots, real)
qats.dump("big48_precision_spec.json", {"job_id":job.job_id(), "recipe":asdict(recipe),
    "seed":spec["seed"], "shots":shots})

# Prepare the fallback on the simulator while the precision job queues/runs.
backup = qats.best_tree_cat(fake, 40)
backup_exp = hc.build_cat_experiment(backup, fake, recipe, seed=3903)
backup_result = backup_exp.run(qats.StableCatSimulator(fake, seed=3903), total_shots=8000)
qats.dump("big40_rehearsal.json", qats.result_dict(backup_result))
print("40-qubit fallback rehearsal:", backup_result, flush=True)

counts = hc.HardwareRunner.counts_from_result(job.result())
result = exp.analyze(counts)
qats.dump("big48_precision_record.json", hc.biggest_cat_record(
    exp, counts, result, where="hardware", job_id=job.job_id()))
print("48-qubit higher-precision hardware:", result, flush=True)
if not result.certified:
    assert backup_result.certified, "Fallback must certify on the simulator before submission"
    for n in (40, 32, 24):
        if n != 40:
            fake_cat = qats.best_tree_cat(fake, n)
            trial = hc.measure_cat_quality(fake_cat, qats.StableCatSimulator(fake, seed=3903+n),
                recipe, total_shots=8000)
            print(f"{n}-qubit rehearsal:",trial,flush=True)
            if not trial.certified:
                continue
        live = qats.best_tree_cat(real, n)
        assert live is not None and hc.verify_cat(live)
        hc.save_circuit(live, f"qats_results/big{n}_live_cat.qpy")
        smaller = hc.build_cat_experiment(live, real, recipe, seed=3903)
        small_shots = smaller.shots_per_circuit(24_000)
        small_job = qats.submit_once(f"big_cat_{n}_fallback", smaller.circuits, small_shots, real)
        qats.dump(f"big{n}_hardware_spec.json", {"job_id":small_job.job_id(), "recipe":asdict(recipe),
            "seed":3903, "shots":small_shots})
        small_counts = hc.HardwareRunner.counts_from_result(small_job.result())
        small_result = smaller.analyze(small_counts)
        qats.dump(f"big{n}_hardware_record.json", hc.biggest_cat_record(
            smaller, small_counts, small_result, where="hardware", job_id=small_job.job_id()))
        print(f"{n}-qubit fallback hardware:", small_result, flush=True)
        if small_result.certified:
            break
