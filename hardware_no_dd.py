"""Predeclared hardware DD ablation, preceded by full-noise simulator checks."""
from dataclasses import replace
from pathlib import Path
import json
from qiskit_ibm_runtime import QiskitRuntimeService
import herding_cats as hc
import qats

real = QiskitRuntimeService().backend("ibm_kingston")
fake = hc.fake_kingston()
original = hc.FinalJob.load("qats_results/final_job.json", real)
recipe = replace(original.team_exp.recipe, dd=None)
fake_prep = hc.load_circuit("my_clean_cat.qpy")
trial = hc.measure_cat_quality(fake_prep, qats.StableCatSimulator(fake, seed=4993),
    recipe, total_shots=12_000, seed=4993)
qats.dump("no_dd_clean_rehearsal.json", qats.result_dict(trial))
print("No-DD clean-cat simulator check:", trial, flush=True)
assert trial.F > 0.5 and hc.verify_cat(original.team_exp.prep)
final = hc.FinalJob(original.team_exp.prep, recipe, real, total_shots=40_000)
final.save("qats_results/final_no_dd_job.json")
job = qats.submit_once("clean_cat_no_dd", final.circuits, final.shots, real)
final.save("qats_results/final_no_dd_job.json", job_id=job.job_id())

big_spec = json.loads(Path("qats_results/big_hardware_spec.json").read_text())
big_recipe = replace(hc.Recipe(**big_spec["recipe"]), dd=None)
big_fake = qats.best_tree_cat(fake, 48)
big_trial = hc.measure_cat_quality(big_fake, qats.StableCatSimulator(fake, seed=5993),
    big_recipe, total_shots=8000, seed=5993)
qats.dump("no_dd_big_rehearsal.json", qats.result_dict(big_trial))
print("No-DD 48-qubit simulator check:", big_trial, flush=True)

precision_path = Path("qats_results/big48_precision_record.json")
already_certified = precision_path.exists() and json.loads(precision_path.read_text())["certified"]
big_job = None
if not already_certified and big_trial.certified:
    prep = hc.load_circuit("big_live_cat.qpy")
    assert hc.verify_cat(prep)
    big_exp = hc.build_cat_experiment(prep, real, big_recipe, seed=big_spec["seed"])
    big_shots = big_exp.shots_per_circuit(40_000)
    big_job = qats.submit_once("big_cat_48_no_dd", big_exp.circuits, big_shots, real)
    qats.dump("big48_no_dd_spec.json", {"job_id":big_job.job_id(), "shots":big_shots})

counts = hc.HardwareRunner.counts_from_result(job.result())
record = final.record(job.job_id(), counts)
qats.dump("hardware_no_dd_record.json", record)
print("No-DD hardware baseline:", final.analyze(counts)[0], flush=True)
print("No-DD hardware clean cat:", final.analyze(counts)[1], flush=True)
print("No-DD hardware R:", record["error_reduction"], flush=True)
if big_job is not None:
    big_counts = hc.HardwareRunner.counts_from_result(big_job.result())
    big_result = big_exp.analyze(big_counts)
    qats.dump("big48_no_dd_record.json", hc.biggest_cat_record(big_exp, big_counts,
        big_result, where="hardware", job_id=big_job.job_id()))
    print("No-DD 48-qubit hardware:", big_result, flush=True)
