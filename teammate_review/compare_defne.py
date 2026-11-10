"""Paired, equal-budget replication; no hardware submissions or credential cells."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import herding_cats as hc
import qats
from qiskit.transpiler import generate_preset_pass_manager
backend=hc.fake_kingston()
ours=hc.load_circuit('qats_results/clean_cat.qpy')
choice=json.loads(Path('qats_results/clean_choice.json').read_text())
defne=generate_preset_pass_manager(optimization_level=3,backend=backend,initial_layout=[135,139,155,154,153,152,151,150,149,148,147,137],seed_transpiler=1).run(qats.make_cat_from_middle(12))
recipe=hc.Recipe(readout_mitigation=True,zne_factors=(1,5),zne_extrapolator='exponential')
rows=[]
for seed in (8101,8102,8103):
 for label,cat,r in [('ours',ours,hc.Recipe(**choice['recipe'])),('Defne',defne,recipe),('our tree + Defne recipe',ours,recipe)]:
  assert hc.verify_cat(cat)
  exp=hc.build_cat_experiment(cat,backend,r,seed=seed)
  result=exp.run(qats.StableCatSimulator(backend,seed=seed),total_shots=26880)
  rows.append(dict(label=label,seed=seed,result=qats.result_dict(result),epsilon=hc.conservative_error(result),circuits=len(exp.circuits),shots=exp.shots_per_circuit(26880)))
  Path('teammate_review/paired_validation.json').write_text(json.dumps(rows,indent=2))
  print(label,seed,result,flush=True)
