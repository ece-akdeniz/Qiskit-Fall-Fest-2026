"""Validate the combined recipe, then run one predeclared hardware comparison."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import herding_cats as hc
import qats
from qiskit_ibm_runtime import QiskitRuntimeService
recipe=hc.Recipe(readout_mitigation=True,zne_factors=(1,5),zne_extrapolator='exponential')
cat=hc.load_circuit('qats_results/clean_cat.qpy')
card=hc.scorecard(cat,recipe,qats.StableCatSimulator(seed=9101),total_shots=26880)
data={k:qats.result_dict(v) if hasattr(v,'F') else v for k,v in card.items()}
Path('teammate_review/combined_scorecard.json').write_text(json.dumps(data,indent=2))
print('Independent combined scorecard:',data,flush=True)
assert card['team'].F>0.5 and hc.verify_cat(cat)
real=QiskitRuntimeService().backend('ibm_kingston')
original=hc.FinalJob.load('qats_results/final_no_dd_job.json',real)
final=hc.FinalJob(original.team_exp.prep,recipe,real,total_shots=40000)
job=qats.submit_once('clean_cat_defne_recipe',final.circuits,final.shots,real)
final.save('qats_results/final_defne_recipe_job.json',job_id=job.job_id())
print('Combined hardware job:',job.job_id(),flush=True)
counts=hc.HardwareRunner.counts_from_result(job.result())
record=final.record(job.job_id(),counts)
qats.dump('hardware_defne_recipe_record.json',record)
print('Combined hardware baseline:',record['baseline']['result'],flush=True)
print('Combined hardware team:',record['team']['result'],flush=True)
